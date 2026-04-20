from flask import Flask, request, render_template, send_file, jsonify
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

ALLOWED_VIDEO = {'mp4', 'mkv', 'avi', 'mov', 'webm'}

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['audio']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    ext = file.filename.rsplit('.', 1)[-1].lower()
    base_name = file.filename.rsplit('.', 1)[0]
    
    # Si es video, convertir a mp3 primero
    if ext in ALLOWED_VIDEO:
        mp3_path = os.path.join(UPLOAD_FOLDER, base_name + '.mp3')
        subprocess.run(['ffmpeg', '-i', filepath, '-q:a', '0', '-map', 'a', mp3_path, '-y'], capture_output=True)
        filepath = mp3_path
    
    result = subprocess.run(['py', '-3.11', '-m', 'demucs', '--mp3', '--out', OUTPUT_FOLDER, filepath], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    
    return jsonify({'status': 'done', 'filename': base_name})

@app.route('/download/<track>/<filename>')
def download(track, filename):
    path = os.path.join(OUTPUT_FOLDER, 'htdemucs', filename, f'{track}.mp3')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)