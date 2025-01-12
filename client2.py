import tkinter as tk
from tkinter import messagebox
import pygame
import socket
import threading
import io
import requests
import os
import wave  # For creating a WAV header

# Initialize pygame
pygame.mixer.init()

# Flask server settings
FLASK_SERVER_URL = "http://127.0.0.1:5000"  # Replace with your Flask server's URL

# UDP settings
UDP_IP = "127.0.0.1"  # Replace with the server's IP address
UDP_PORT = 5005       # Replace with the server's port

# Global variable to track if audio is paused
is_paused = False

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

# Function to receive audio data via UDP
def receive_audio(track_id):
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        print(f"Socket bound to {UDP_IP}:{UDP_PORT}")  # Debugging line

        print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

        # Open a BytesIO object to store the received audio data
        audio_data = io.BytesIO()

        while True:
            data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
            if not data:  # Empty packet signals the end of the stream
                print("Received end-of-stream marker.")  # Debugging line
                break  # End of stream
            print(f"Received {len(data)} bytes from {addr}")  # Debugging line
            audio_data.write(data)

        # Close the socket
        sock.close()
        print("Socket closed.")  # Debugging line

        # Create the Tempo folder if it doesn't exist
        tempo_folder = "Tempo"
        print(f"Current working directory: {os.getcwd()}")  # Debugging line
        if not os.path.exists(tempo_folder):
            print(f"Creating folder: {tempo_folder}")  # Debugging line
            os.makedirs(tempo_folder)
            print(f"Folder created: {tempo_folder}")  # Debugging line
        else:
            print(f"Folder already exists: {tempo_folder}")  # Debugging line

        # Save the received data to a file in the Tempo folder
        file_path = os.path.join(tempo_folder, f"received_audio_{track_id}.wav")
        with open(file_path, "wb") as f:
            f.write(audio_data.getvalue())  # Write the contents of BytesIO to the file
        print(f"Audio saved to {file_path}")  # Debugging line

        # Add a WAV header to the received audio data
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)  # 44.1 kHz
            wav_file.writeframes(audio_data.getvalue())

        # Rewind the buffer
        wav_buffer.seek(0)

        # Play the audio using pygame
        pygame.mixer.music.load(wav_buffer)
        print("Audio data loaded into Pygame.")  # Debugging line
        pygame.mixer.music.play()
        print("Playing audio...")  # Debugging line
        while pygame.mixer.music.get_busy():  # Wait until the audio finishes playing
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Error receiving data: {e}")  # Debugging line
        messagebox.showerror("Error", str(e))

# Function to play the selected track
def play_selected_track():
    selected_track_index = track_listbox.curselection()  # Get the selected track index
    if selected_track_index:
        selected_track_id = selected_track_index[0]  # Get the first selected index
        # Send an HTTP request to the Flask server to start streaming the selected track
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/stream/{selected_track_id}")
            if response.status_code == 200:
                print(f"Requested track {selected_track_id} from the server.")
            else:
                messagebox.showerror("Error", f"Failed to request track {selected_track_id} from the server.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        # Start a new thread to receive and play the audio
        threading.Thread(target=receive_audio, args=(selected_track_id,)).start()

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

# Set window size and make it non-resizable
root.geometry("800x600")
root.resizable(False, False)

# Set background color
root.configure(bg="#121212")

# Title and description
title_label = tk.Label(
    root,
    text="Audio Stream Client",
    font=("Arial", 24, "bold"),
    bg="#121212",
    fg="#1DB954"
)
title_label.pack(pady=20)

description_label = tk.Label(
    root,
    text="Select a track to stream and control audio playback.",
    font=("Arial", 14),
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
    selectforeground="#FFFFFF",   # White selection text
    height=10
)
for track_name in track_list:
    track_listbox.insert(tk.END, track_name)  # Add track names to the listbox
track_listbox.pack(pady=20, fill=tk.BOTH, expand=True)

# Button frame
button_frame = tk.Frame(root, bg="#121212")
button_frame.pack(pady=20)

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