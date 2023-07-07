import requests
from speaker_recognition import AudioProcessor
import argparse

LOCALHOST = 'http://127.0.0.1:8080/recognition'

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

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',
                        '--audio_path',
                        default=None,
                        help="Path of audio file to send",
                        type=str)
    parser.add_argument('-i',
                        '--ip',
                        default=VM_IP,
                        help='API URL',
                        type=str)
    args = parser.parse_args()

    TEST_WAV = args.audio_path
    IP = args.ip

    # ap = AudioProcessor()
    saved = TEST_WAV
    # saved = ap.splitter(2500, 3500, TEST_WAV)
    # saved = ap.concater([TEST_WAV for _ in range(5)])
    res = send_test_audio(saved, url=IP)
    print(res.text)
