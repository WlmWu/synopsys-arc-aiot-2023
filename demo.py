import requests
from speaker_recognition import AudioProcessor

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

    ap = AudioProcessor()

    # ap.get_audio_length(TEST_WAV)
    # ap.splitter(2000, 4000, TEST_WAV)
    # ap.concater([TEST_WAV for _ in range(5)])

    # res = send_test_audio(TEST_WAV)
    # print(res.text)

    saved = TEST_WAV
    # saved = ap.splitter(2500, 3500, TEST_WAV)
    # saved = ap.concater([TEST_WAV for _ in range(5)])
    res = send_test_audio(saved, url=VM_IP)
    print(res.text)
