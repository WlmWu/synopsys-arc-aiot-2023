import io
import os
import sys
import wave
import logging
import traceback
from logging.config import dictConfig
from datetime import datetime
from dynacloud import service
from werkzeug.exceptions import HTTPException
from google.api_core.exceptions import GoogleAPICallError
from flask import Flask, jsonify, json, request, make_response, abort, send_file, render_template

from datetime import datetime
import pytz
from pathlib import Path
import threading

from speaker_recognition.recognizer import SpeakerRecognizer
from speaker_recognition.database import DBMananger
from speaker_recognition.audio_processor import AudioProcessor
from speaker_recognition.notification import Notifier
from speaker_recognition.config import TIME_ZONE, TIME_FORMAT


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webep'}
ALLOWED_AUDIO_EXTENSIONS = {'wav'}
ALLOWED_RAW_AUDIO_EXTENSIONS = {'log', 'txt'}

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': sys.stdout,
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

sr = SpeakerRecognizer()
dbm = DBMananger()
ap = AudioProcessor()
nfr = Notifier()

app = Flask(__name__, template_folder='template', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1000 * 1000
app.config['AUDIO_UNKNOWN_PATH'] = '.'
app.config['AUDIO_TMP_FILENAME'] = 'unknown.wav'
app.config['RAW_AUDIO_TMP_FILENAME'] = 'unknown.log'


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()

    # replace the body with JSON
    response.content_type = "application/json"
    response.data = json.dumps({"errors": [e.description]})

    return response


@app.errorhandler(GoogleAPICallError)
def handle_google_api_error(e):
    logging.warning(e.message)
    return make_response(jsonify({"errors": [e.message]}), e.code)


@app.errorhandler(Exception)
def handle_exceptions(e):
    filename, line_num, func_name, text = traceback.extract_tb(e.__traceback__)[-1]
    logging.info(e)
    logging.info(f'Exception;main;{type(e).__name__};MSG;{str(e)};FILE;{filename};LINE;{line_num};FUNC;{func_name};TEXT;{text}')

    return make_response(jsonify({"errors": ['Internal Server Error']}), 500)


@app.before_request
def before_request():
    auth_header = request.headers.get('Authorization')
    token = service.parse_token_from_auth_header(auth_header)
    service.check_auth_token_is_valid(token)


def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def allowed_raw_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RAW_AUDIO_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    return jsonify({'data': 'Hello AIoT!'})


@app.route('/vision', methods=['POST'])
def vision():
    file = request.files.get('image')

    if not file:
        abort(422, 'Please upload the image using the image parameter.')
    if file.filename == '' or not allowed_image_file(file.filename):
        abort(422, 'Unsupported image type.')

    content = file.read()
    data = service.detect_text(content)

    return jsonify({'data': data})


@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    text = request.form.get('text')

    if not text:
        abort(422, 'The parameter `text` is required.')
    if len(text.encode('utf-8')) >= 5000:
        abort(422, 'The text string must < 5,000 bytes')
    data = service.text_to_speech(text)

    name = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    return send_file(io.BytesIO(data), mimetype="audio/x-wav", as_attachment=True, download_name=name)


@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    file = request.files.get('audio')

    if not file:
        abort(422, 'Please upload the audio using the audio parameter.')
    if file.filename == '' or not allowed_audio_file(file.filename):
        abort(422, 'Unsupported audio type.')

    content = file.read()
    with wave.open(io.BytesIO(content)) as wav:
        duration_seconds = wav.getnframes() / wav.getframerate()
        if duration_seconds >= 60:
            abort(422, 'The duration_seconds of audio is too long (> 60 seconds).')

    data = service.speech_to_text(content)

    return jsonify({'data': data})

@app.route('/recognition',methods=['GET','POST'])
def recognition():
    if request.method == 'POST':
        # print(request.headers)
        f = request.files.get('audio')
        if not f:
            abort(422, 'Please upload the audio using the audio parameter.')
        if f.filename == '' or (not allowed_audio_file(f.filename) and not allowed_raw_audio_file(f.filename)):
            abort(422, 'Unsupported audio/raw audio type. (.wav/.log/.txt)')
        
        if allowed_audio_file(f.filename):
            with open(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['AUDIO_TMP_FILENAME'], 'wb') as wav:
                wav.write(f.read())
        elif allowed_raw_audio_file(f.filename):
            try:
                with open(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['RAW_AUDIO_TMP_FILENAME'], 'wb') as wav:
                    wav.write(f.read())
                ap.raw_to_wav(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['RAW_AUDIO_TMP_FILENAME'])
            except:
                abort(422, 'Content format is not correct.')
            
        res = sr.recognize(Path(app.config['AUDIO_UNKNOWN_PATH']))
        current_time = datetime.now(pytz.timezone(TIME_ZONE)).strftime(TIME_FORMAT)
        
        threads = []
        threads.append(threading.Thread(target=nfr.send_clocked_in_out_email, args=(res, current_time,)))
        threads.append(threading.Thread(target=dbm.clock_in, args=(dict(eid=res if res is not sr.unknown else -1, time_in=current_time),)))
        for t in threads:
            t.start()
        
        # print(res)
        return jsonify({'EID': str(res)})
    else:
        return jsonify({'data': 'Please using POST method'})

@app.route('/database')
def dbview():
    employees, timestamps = dbm.get_all_enrolled(), dbm.get_all_timestamps()
    table = lambda table_name, data, index: dict(table_name=table_name, data=data, index=index)
    employees = table("Employees", data=employees, index=False)
    timestamps = table("Timestamps", data=timestamps, index=True)
    return render_template('index.html', employees=employees, timestamps=timestamps)

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=True, port=server_port, host='0.0.0.0')
