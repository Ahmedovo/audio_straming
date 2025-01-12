from flask import Flask, jsonify
import os
import socket
import threading

app = Flask(__name__)

# Path to the music folder
MUSIC_FOLDER = "music"  # Replace with your folder path
playlist = []  # List to store the paths of audio files

# UDP settings
UDP_IP = "127.0.0.1"  # Replace with the client's IP address
UDP_PORT = 5005       # Replace with the client's port

# Load the playlist
def load_playlist():
    global playlist
    playlist = [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.endswith(".wav")]
    if not playlist:
        print("No .wav files found in the music folder.")
    else:
        print("Playlist loaded successfully:")
        for track in playlist:
            print(track)

# Function to stream audio via UDP
def stream_audio(track_id):
    if track_id < 0 or track_id >= len(playlist):
        print("Invalid track ID")
        return

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Streaming track {track_id} via UDP to {UDP_IP}:{UDP_PORT}")

    try:
        with open(playlist[track_id], "rb") as f:
            while True:
                chunk = f.read(1024)  # Read in chunks of 1024 bytes
                if not chunk:
                    break  # End of file
                sock.sendto(chunk, (UDP_IP, UDP_PORT))
                print(f"Sent {len(chunk)} bytes to {UDP_IP}:{UDP_PORT}")  # Debugging line

        # Send an empty packet to signal the end of the stream
        sock.sendto(b"", (UDP_IP, UDP_PORT))
        print("Sent end-of-stream marker.")  # Debugging line
    finally:
        sock.close()
        print("Finished streaming.")  # Debugging line

# Flask route to start streaming
@app.route('/stream/<int:track_id>')
def start_stream(track_id):
    if track_id < 0 or track_id >= len(playlist):
        return "Invalid track ID", 404

    # Start streaming in a new thread
    threading.Thread(target=stream_audio, args=(track_id,)).start()
    return f"Started streaming track {track_id} via UDP to {UDP_IP}:{UDP_PORT}"

# Flask route to fetch the list of tracks
@app.route('/tracks')
def get_tracks():
    return jsonify([os.path.basename(track) for track in playlist])

if __name__ == "__main__":
    load_playlist()
    app.run(host="0.0.0.0", port=5000)