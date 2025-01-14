import tkinter as tk
from tkinter import messagebox
import pygame
import socket
import threading
import requests
import wave  # For creating a WAV header
import os  # For handling file paths and directories

# Initialize pygame
pygame.mixer.init()

# Flask server settings
FLASK_SERVER_URL = "http://192.168.0.106:5000"  # Replace with your Flask server's IP and port

# UDP settings
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5005     # Default UDP port for the client

# Global variable to track if audio is paused
is_paused = False

# Create the 'tempo' folder if it doesn't exist
if not os.path.exists("tempo"):
    os.makedirs("tempo")

# Function to stop the currently playing audio
def stop_audio():
    pygame.mixer.music.stop()
    print("Audio stopped.")  # Debugging line

# Function to pause the currently playing audio
def pause_audio():
    global is_paused
    if pygame.mixer.music.get_busy():  # Check if audio is playing
        pygame.mixer.music.pause()
        is_paused = True
        print("Audio paused.")  # Debugging line

# Function to resume the paused audio
def resume_audio():
    global is_paused
    if is_paused:  # Check if audio is paused
        pygame.mixer.music.unpause()
        is_paused = False
        print("Audio resumed.")  # Debugging line

# Function to receive audio data via UDP and play it directly
def receive_audio():
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        print(f"Socket bound to {UDP_IP}:{UDP_PORT}")  # Debugging line

        print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

        # Initialize pygame mixer with a buffer size
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

        # Open a BytesIO object to store the received audio data temporarily
        audio_data = io.BytesIO()

        # Read the first packet to get the WAV header
        data, addr = sock.recvfrom(4096)  # Buffer size is 4096 bytes
        audio_data.write(data)

        # Extract the WAV header from the first packet
        audio_data.seek(0)
        with wave.open(audio_data, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()

        # Initialize pygame mixer with the correct parameters
        pygame.mixer.init(frequency=frame_rate, size=-16 if sample_width == 2 else -8, channels=channels, buffer=4096)

        # Create a new BytesIO object for streaming
        audio_stream = io.BytesIO()

        # Write the WAV header to the stream
        with wave.open(audio_stream, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(frame_rate)

        # Start playing the audio stream
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()

        # Continue receiving and playing audio data
        while True:
            data, addr = sock.recvfrom(4096)  # Buffer size is 4096 bytes
            if not data:  # Empty packet signals the end of the stream
                print("Received end-of-stream marker.")  # Debugging line
                break  # End of stream
            print(f"Received {len(data)} bytes from {addr}")  # Debugging line
            audio_stream.write(data)
            pygame.mixer.music.queue(audio_stream)

        # Close the socket
        sock.close()
        print("Socket closed.")  # Debugging line

    except Exception as e:
        print(f"Error receiving data: {e}")  # Debugging line
        messagebox.showerror("Error", str(e))

# Function to play the selected track
def play_selected_track():
    selected_track_index = track_listbox.curselection()  # Get the selected track index
    if selected_track_index:
        selected_track_id = selected_track_index[0]  # Get the first selected index

        # Get the client's IP address dynamically
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to Google's public DNS server
        client_ip = s.getsockname()[0]  # Get the IP address of the interface used
        s.close()
        client_port = UDP_PORT

        # Send an HTTP request to the Flask server to start streaming the selected track
        try:
            response = requests.get(
                f"{FLASK_SERVER_URL}/stream/{selected_track_id}",
                params={"ip": client_ip, "port": client_port}
            )
            if response.status_code == 200:
                print(f"Requested track {selected_track_id} from the server.")
            else:
                messagebox.showerror("Error", f"Failed to request track {selected_track_id} from the server.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        # Start a new thread to receive and play the audio
        threading.Thread(target=receive_audio).start()

# Fetch the list of tracks from the server
def fetch_track_list():
    try:
        response = requests.get(f"{FLASK_SERVER_URL}/tracks")
        if response.status_code == 200:
            return response.json()  # Assume the server returns a JSON list of track names
        else:
            messagebox.showerror("Error", "Failed to fetch track list from the server.")
            return []
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return []

# Tkinter GUI
root = tk.Tk()
root.title("Audio Stream Client")

# Set window size and make it resizable
root.geometry("1024x768")
root.resizable(True, True)

# Set background color
root.configure(bg="#121212")

# Title and description
title_label = tk.Label(
    root,
    text="Audio Stream Client",
    font=("Arial", 30, "bold"),
    bg="#121212",
    fg="#1DB954"
)
title_label.pack(pady=20)

description_label = tk.Label(
    root,
    text="Select a track to stream and control audio playback.",
    font=("Arial", 18),
    bg="#121212",
    fg="#FFFFFF"
)
description_label.pack(pady=10)

# Fetch the list of tracks from the server
track_list = fetch_track_list()

# Listbox for track selection
track_listbox = tk.Listbox(
    root,
    selectmode=tk.SINGLE,  # Allow single selection
    font=("Arial", 14),
    bg="#181818",
    fg="#FFFFFF",
    selectbackground="#1DB954",  # Spotify green selection background
    selectforeground="#FFFFFF",   # White selection text,
    height=10
)
for track_name in track_list:
    track_listbox.insert(tk.END, track_name)  # Add track names to the listbox
track_listbox.pack(pady=20, fill=tk.BOTH, expand=True)

# Button frame
button_frame = tk.Frame(root, bg="#121212")
button_frame.pack(pady=20, fill=tk.X)

# Play button
play_button = tk.Button(
    button_frame,
    text="Play Selected Track",
    command=play_selected_track,
    bg="#1DB954",  # Spotify green
    fg="white",
    font=("Arial", 14),
    width=20,
    bd=0,
    padx=10,
    pady=10
)
play_button.grid(row=0, column=0, padx=10, pady=5)

# Pause button
pause_button = tk.Button(
    button_frame,
    text="Pause",
    command=pause_audio,
    bg="#1DB954",  # Spotify green
    fg="white",
    font=("Arial", 14),
    width=20,
    bd=0,
    padx=10,
    pady=10
)
pause_button.grid(row=0, column=1, padx=10, pady=5)

# Resume button
resume_button = tk.Button(
    button_frame,
    text="Resume",
    command=resume_audio,
    bg="#1DB954",  # Spotify green
    fg="white",
    font=("Arial", 14),
    width=20,
    bd=0,
    padx=10,
    pady=10
)
resume_button.grid(row=0, column=2, padx=10, pady=5)

# Stop button
stop_button = tk.Button(
    button_frame,
    text="Stop",
    command=stop_audio,
    bg="#1DB954",  # Spotify green
    fg="white",
    font=("Arial", 14),
    width=20,
    bd=0,
    padx=10,
    pady=10
)
stop_button.grid(row=0, column=3, padx=10, pady=5)

root.mainloop()