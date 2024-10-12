from flask import Flask, render_template, request, send_from_directory, redirect
import os
import json
from datetime import datetime
from urllib.parse import quote

app = Flask(__name__)

SONG_FOLDER = '/home/server/music_player/music'
SONG_INFO_FILE = '/home/server/music_player/data/song_info.json'

# Ensure the data directory and JSON file exist
if not os.path.exists(os.path.dirname(SONG_INFO_FILE)):
    os.makedirs(os.path.dirname(SONG_INFO_FILE))

if not os.path.isfile(SONG_INFO_FILE):
    with open(SONG_INFO_FILE, 'w') as f:
        json.dump({}, f)

@app.route('/')
def index():
    song_files = [f for f in os.listdir(SONG_FOLDER) if os.path.isfile(os.path.join(SONG_FOLDER, f))]
    return render_template('index.html', songs=song_files)

@app.route('/play/<filename>')
def play(filename):
    # Make sure to unquote the filename for file system access
    full_path = os.path.join(SONG_FOLDER, filename)
    update_song_info(filename, get_song_info(filename)['plays'] + 1, get_song_info(filename)['rating'])
    return send_from_directory(SONG_FOLDER, filename)

@app.route('/song/<filename>')
def song(filename):
    filename = filename.split('/')[-1]
    song_info = {}
    try:
        with open(SONG_INFO_FILE, 'r') as f:
            song_info = json.load(f)
    except Exception as e:
        print(f"Error reading song info: {e}")

    info = song_info.get(filename, {'plays': 0, 'rating': 0, 'daily_plays': {}})
    
    # Ensure `daily_plays` is a dictionary
    info['daily_plays'] = info.get('daily_plays', {})
    
    return render_template('song.html', filename=filename, song_info=info)

@app.route('/rate/<filename>', methods=['POST'])
def rate_song(filename):
    rating = request.form.get('rating', 0, type=int)
    with open(SONG_INFO_FILE, 'r') as f:
        data = json.load(f)
    if filename in data:
        data[filename]['rating'] = rating
    else:
        data[filename] = {'plays': 0, 'rating': rating, 'daily_plays': {}}
    with open(SONG_INFO_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return redirect(f'/song/{filename}')

def get_song_info(filename):
    try:
        with open(SONG_INFO_FILE, 'r') as f:
            song_info = json.load(f)
    except FileNotFoundError:
        song_info = {}
    return song_info.get(filename, {'plays': 0, 'rating': 0, 'daily_plays': {}})

def update_song_info(filename, plays, rating):
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Load existing song info or create an empty dictionary if it doesn't exist
    if os.path.exists(SONG_INFO_FILE):
        with open(SONG_INFO_FILE, 'r') as f:
            song_info = json.load(f)
    else:
        song_info = {}

    # Ensure the song entry exists in the song_info file
    if filename not in song_info:
        song_info[filename] = {
            'plays': 0,
            'rating': 0,
            'daily_plays': {}
        }

    # Ensure the 'daily_plays' key exists in the song entry
    if 'daily_plays' not in song_info[filename]:
        song_info[filename]['daily_plays'] = {}

    # Update plays count and daily plays
    song_info[filename]['plays'] = plays
    song_info[filename]['daily_plays'][today] = song_info[filename]['daily_plays'].get(today, 0) + 1
    song_info[filename]['rating'] = rating

    # Save the updated song info back to the file
    with open(SONG_INFO_FILE, 'w') as f:
        json.dump(song_info, f, indent=4)

    return song_info[filename]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

