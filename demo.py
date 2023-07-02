import requests

from typing import List, Union

import os
from pathlib import Path
from pydub import AudioSegment
import wave
import contextlib

LOCALHOST = 'http://127.0.0.1:8080/recognition'

class AudioManager():
    def __init__(self) -> None:
        pass

    def splitter(self, t1, t2, audio: Path) -> str:
        # t1, t2: milliseconds
        output = AudioSegment.from_wav(audio)
        output = output[t1:t2]
        outfile = f'{str(audio)[:-4]}_{t1}_{t2}.wav'
        output.export(outfile, format="wav")

        print(f'Saved as {outfile}')
        return outfile

    def concater(self, audios: List[Union[str, Path]]):
        type_str_or_path = lambda s: (type(s) is str) or (type(s) is Path)
        for audio in audios:
            if type_str_or_path(audio):
                audio = Path(audio)
            else:
                return TypeError

        infiles = audios
        outfile = Path(audios[0]).parent.resolve() / f"{'_'.join(list(map(lambda a: os.path.basename(a).split('.')[0], audios)))}.wav"

        data= []
        for infile in infiles:
            with wave.open(str(infile), 'rb') as w:
                data.append([w.getparams(), w.readframes(w.getnframes())])
            
        with wave.open(str(outfile), 'wb') as output:
            output.setparams(data[0][0])
            for i in range(len(data)):
                output.writeframes(data[i][1])

        print(f"Saved as {outfile}")
        return str(outfile)

    def get_audio_length(self, audio: Path) -> float:
        with contextlib.closing(wave.open(audio,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
        
        duration = frames / float(rate)
        print(duration)
        return duration



def send_test_audio(audio, url=LOCALHOST) -> requests.Response:
    headers = {
        "Authorization": "Bearer %_put_your_auth_token_here_%",
    }
    with open(audio, 'rb') as file:
        files = {'audio': file}
        p = requests.Request('POST', url=url, headers=headers, files=files).prepare()
        pretty_print_POST(p)
        s = requests.Session()
        r = s.send(p, verify=False)
    
    return r

def pretty_print_POST(req):
    with open('payload.txt', 'w') as f:
        s = '{}\r\n{}\r\n\r\n{}'.format(
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
        )
        f.write(s)

if __name__ == '__main__':
    VM_IP = 'https://35.221.137.170/recognition'
    VM_IP = LOCALHOST

    TEST_WAV = 'p225_037.wav'
    # TEST_WAV = 'p226_017.wav'
    # TEST_WAV = 'p228_025.wav'

    # TEST_WAV = 'p228_025_1500_2500.wav'
    # TEST_WAV = 'p225_037_2000_3000_.wav'
    # TEST_WAV = 'p225_037_2000_4000.wav'

    # TEST_WAV = 'p225_037_1500_2500.wav'
    # TEST_WAV = 'p225_037_1500_2500_5times.wavs'

    # TEST_WAV = 'p225_037_2500_3000.wav'
    # TEST_WAV = 'p225_037_2500_3000_5times.wav'

    # TEST_WAV = 'p225_037_2500_3500.wav'
    # TEST_WAV = 'p225_037_2500_3500_5times.wav'

    alm = AudioManager()

    # alm.get_audio_length(TEST_WAV)
    # alm.splitter(2000, 4000, TEST_WAV)
    # alm.concater([TEST_WAV for _ in range(5)])

    # res = send_test_audio(TEST_WAV)
    # print(res.text)

    saved = TEST_WAV
    # saved = alm.splitter(2500, 3500, TEST_WAV)
    # saved = alm.concater([TEST_WAV for _ in range(5)])
    res = send_test_audio(saved, url=VM_IP)
    print(res.text)
