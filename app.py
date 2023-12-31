from flask import Flask, jsonify, request, render_template
from datetime import datetime
import pytz
import os
from pathlib import Path
import threading

from speaker_recognition import SpeakerRecognizer, DBMananger, AudioProcessor, Notifier
from speaker_recognition import TIME_ZONE, TIME_FORMAT


sr = SpeakerRecognizer()
dbm = DBMananger()
ap = AudioProcessor()
nfr = Notifier()

app = Flask(__name__, template_folder='template', static_folder='static')
app.config['AUDIO_UNKNOWN_PATH'] = '.'
app.config['AUDIO_TMP_FILENAME'] = 'unknown.wav'
app.config['RAW_AUDIO_TMP_FILENAME'] = 'unknown.log'


def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav'}

def allowed_raw_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'log', 'txt'}

@app.route('/')
def index():
    employees, timestamps = dbm.get_all_enrolled(), dbm.get_all_timestamps()
    table = lambda table_name, data, index: dict(table_name=table_name, data=data, index=index)
    employees = table("Employees", data=employees, index=False)
    timestamps = table("Timestamps", data=timestamps, index=True)
    return render_template('index.html', employees=employees, timestamps=timestamps)

@app.route('/recognition',methods=['GET','POST'])
def recognition():
    if request.method == 'POST':
        # print(request.headers)
        f = request.files.get('audio')
        
        if allowed_audio_file(f.filename):
            with open(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['AUDIO_TMP_FILENAME'], 'wb') as wav:
                wav.write(f.read())
        elif allowed_raw_audio_file(f.filename):
            try:
                with open(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['RAW_AUDIO_TMP_FILENAME'], 'wb') as wav:
                    wav.write(f.read())
                ap.raw_to_wav(Path(app.config['AUDIO_UNKNOWN_PATH']) / app.config['RAW_AUDIO_TMP_FILENAME'])
            except:
                return 'Content format is not correct.'
            
        res = sr.recognize(Path(app.config['AUDIO_UNKNOWN_PATH']))
        current_time = datetime.now(pytz.timezone(TIME_ZONE)).strftime(TIME_FORMAT)

        threads = []
        threads.append(threading.Thread(target=nfr.send_clocked_in_out_email, args=(res, current_time,)))
        threads.append(threading.Thread(target=dbm.clock_in, args=(dict(eid=res if res is not sr.unknown else -1, time_in=current_time),)))
        for t in threads:
            t.start()
        # for t in threads:
        #     t.join()        

        # print(res)
        return jsonify({'EID': str(res)})
    else:
        return jsonify({'data': 'Please using POST method'})

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=True, port=server_port, host='0.0.0.0')