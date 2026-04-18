from flask import Flask, send_from_directory, abort
import os

app = Flask(__name__, static_folder=None)

# The root directory of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@app.route('/')
def index():
    # Failsafe path searching for the main viewer
    search_dirs = [
        os.path.dirname(__file__),               # Next to this script
        os.path.join(BASE_DIR, 'QuestViewer'),   # Original structure
        BASE_DIR,                                # One folder up
        os.getcwd()                              # Current terminal location
    ]
    for directory in search_dirs:
        if os.path.exists(os.path.join(directory, 'node_viewer.html')):
            return send_from_directory(directory, 'node_viewer.html')
    abort(404)

@app.route('/<path:filename>')
def serve_file(filename):
    # Failsafe path searching for JSON files (quest_library.json/quest_lines.json)
    search_dirs = [
        os.path.dirname(__file__),               # Next to this script
        os.path.join(BASE_DIR, 'QuestViewer'),   # Original structure
        BASE_DIR,                                # One folder up
        os.getcwd()                              # Current terminal location
    ]
    for directory in search_dirs:
        if os.path.exists(os.path.join(directory, filename)):
            return send_from_directory(directory, filename)
    abort(404)

if __name__ == '__main__':
    print(f"Starting Waitress server on PORT 8003 (Accessible on all IPs)")
    print(f"Base Directory: {BASE_DIR}")
    from waitress import serve
    serve(app, host='0.0.0.0', port=8003)
