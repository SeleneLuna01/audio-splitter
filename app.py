from flask import Flask, request, render_template, send_file, jsonify, Response
import os
import subprocess
import re
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_VIDEO = {'mp4', 'mkv', 'avi', 'mov', 'webm'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    print(request.form)
    print(request.files)
    model = request.form.get('model', 'htdemucs')
    file = request.files['audio']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    ext = file.filename.rsplit('.', 1)[-1].lower()
    base_name = file.filename.rsplit('.', 1)[0]

    if ext in ALLOWED_VIDEO:
        mp3_path = os.path.join(UPLOAD_FOLDER, base_name + '.mp3')
        subprocess.run(['ffmpeg', '-i', filepath, '-q:a', '0', '-map', 'a', mp3_path, '-y'], capture_output=True)
        filepath = mp3_path

    def generate(model, filepath, base_name):
        try:
            process = subprocess.Popen(
                ['py', '-3.11', '-m', 'demucs', '--mp3', '--two-stems', 'vocals', '-n', model, '--out', OUTPUT_FOLDER, filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                match = re.search(r'(\d+)%', line)
                if match:
                    percent = int(match.group(1))
                    yield f"data: {json.dumps({'progress': percent})}\n\n"
            process.wait()
            yield f"data: {json.dumps({'progress': 100, 'status': 'done', 'filename': base_name})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(model, filepath, base_name), mimetype='text/event-stream')

@app.route('/download/<track>/<filename>')
def download(track, filename):
    path = os.path.join(OUTPUT_FOLDER, 'htdemucs', filename, f'{track}.mp3')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)