import os
from pathlib import Path
from typing import List, Union, Optional

from pydub import AudioSegment
import wave
import contextlib
from scipy.io.wavfile import write
import numpy as np
import math

class AudioProcessor():
    def __init__(self) -> None:
        pass

    def splitter(self, t1, t2, audio: Union[str, Path]) -> str:
        # t1, t2: milliseconds
        output = AudioSegment.from_wav(audio)
        output = output[t1:t2]
        outfile = f'{str(audio)[:-4]}_{t1}_{t2}.wav'
        output.export(outfile, format="wav")

        print(f'Saved as {outfile}')
        return outfile

    def concater(self, audios: List[Union[str, Path]], outfile: Optional[Union[str, Path]] = None) -> str:
        for audio in audios:
            if isinstance(audio, Path) or isinstance(audio, str):
                audio = Path(audio)
            else:
                raise TypeError

        infiles = audios
        if outfile is None:
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

    def get_audio_length(self, audio: Union[str, Path]) -> float:
        with contextlib.closing(wave.open(str(audio),'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
        
        duration = frames / float(rate)     # sec
        return duration
    
    def raw_to_wav(self, audio: Union[str, Path], samplerate=16000) -> str: 
        data_input = np.genfromtxt(audio, delimiter=',')
        data_input = data_input.T
        left_channel, right_channel = data_input[0], data_input[1]
        dual_channel = left_channel + right_channel
        dual_channel = dual_channel / 2

        outfile = Path(audio).parent.resolve() / f"{os.path.basename(audio).split('.')[0]}.wav"
        write(outfile, samplerate, dual_channel.astype(np.int16))
        
        print(f"Saved as {outfile}")
        return str(outfile)

    def audio_padding(self, audio: Union[str, Path], min_audio_len: float = 2.) -> str:
        # min_audio_len: sec
        audio_length = self.get_audio_length(audio)
        if audio_length < min_audio_len:
            audio = self.concater([audio for _ in range(math.ceil(min_audio_len / audio_length))], audio)
        return audio

if __name__ == '__main__':
    ap = AudioProcessor()

    # TEST_WAV = 'unknown.wav'

    TEST_LOG = 'pdm_dual.log'
    TEST_WAV = f"{os.path.basename(TEST_LOG).split('.')[0]}.wav"
    ap.raw_to_wav(TEST_LOG)

    saved = TEST_WAV
    saved = ap.splitter(2500, 3000, TEST_WAV)
    saved = ap.concater([TEST_WAV for _ in range(2)])
    ap.get_audio_length(saved)
    