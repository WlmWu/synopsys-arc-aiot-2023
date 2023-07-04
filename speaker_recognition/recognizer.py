from resemblyzer import preprocess_wav, VoiceEncoder
from itertools import groupby
from pathlib import Path
from tqdm import tqdm
import numpy as np
from typing import Union
import argparse
import os
import math

from .config import DATABASE_PATH, ENROLLED_EMBEDDINGS_PATH, DB_NAME
from .database import DBMananger
from .audio_processor import AudioProcessor

class SpeakerRecognizer():
    def __init__(self, embeddings_path=Path(DATABASE_PATH) / ENROLLED_EMBEDDINGS_PATH) -> None:
        self._encoder = VoiceEncoder()
        self._dbm = DBMananger()
        self._ap = AudioProcessor()

        self._embeddings_path = embeddings_path

        self._threshold = 0.85
    
    @property
    def unknown(self):
        return 'unknown' 
    

    def audio_preprocess(self, new_audio_path: Union[str, Path]):
        audio_paths = list(Path(new_audio_path).glob("*.wav"))

        wavs_preprocessed_dict = {speaker: list(map(preprocess_wav, wav_fpaths)) for speaker, wav_fpaths in 
                            groupby(tqdm(audio_paths, "Preprocessing wavs", len(audio_paths), unit="wavs"), 
                                lambda wav_fpath: wav_fpath.parent.stem)}
        
        wav_fname = list(wavs_preprocessed_dict.keys())[0]
        wavs = list(wavs_preprocessed_dict.values())[0]

        return wav_fname, wavs
    
    def recognize(self, new_audio_path: Union[str, Path]) -> str:
        self._ap.audio_padding(list(Path(new_audio_path).glob("*.wav"))[0], 2)
        _, wavs = self.audio_preprocess(new_audio_path)
        embeddings = self._encoder.embed_utterance(wavs[0])

        id_pred, similarity = self.unknown, 0
        for enrolled_embeddings_data in self.get_all_embeddings_saved():
            enrolled_speaker_id = enrolled_embeddings_data['EID']
            embeddings_path = self._embeddings_path / enrolled_embeddings_data['feature_path']
            enrolled_embeddings = self.get_embeddings_saved(embeddings_path)
            similarity_matrix = np.inner(embeddings, enrolled_embeddings)
            print(enrolled_speaker_id, ':', similarity_matrix)

            if similarity_matrix > similarity:
                similarity = similarity_matrix
                id_pred = enrolled_speaker_id

        return id_pred if similarity > self._threshold else self.unknown
    
    
    def enrolled_new(self, new_employee_name: str, new_audio_path: Union[str, Path], new_employee_email='test@nycu.edu'):
        wav_fname, wavs = self.audio_preprocess(new_audio_path)

        speaker_id = self._dbm.get_new_eid()
        saved_path = self._embeddings_path / f'{speaker_id}.npy'
        employee = dict(name=wav_fname if new_employee_name is None else new_employee_name, email=new_employee_email, feature_path=f'{speaker_id}.npy')
        
        self._dbm.enroll_new(employee)

        embeddings = self._encoder.embed_speaker(wavs)
        np.save(saved_path, embeddings)

        print(f'Saved: {saved_path}')
    
    def get_embeddings_saved(self, saved_path: Union[str, Path]) -> np.ndarray:
        return np.load(saved_path)
    
    def get_all_embeddings_saved(self) -> dict():
        enrolled_db_data = self._dbm.get_all_enrolled()
        return enrolled_db_data



if __name__ == '__main__':
    sr = SpeakerRecognizer()
    parser = argparse.ArgumentParser()
    parser.add_argument('-n',
                        '--newpath',
                        default=None,
                        help="Path of audio files for newly enrolled employee",
                        type=str)
    args = parser.parse_args()

    # # Enroll a new speaker
    # # new_audio_folder contains only *.wav

    if args.newpath is not None:
        new_path = args.newpath
        audio_path = Path(new_path).parent.resolve()
        new_audio_folder = os.path.basename(new_path)
        sr.enrolled_new(new_audio_folder, audio_path / new_audio_folder)


    # # Recognize speaker
    # # One file only in TEST_PATH and is *.wav

    # TEST_PATH = Path('./test_audio')
    # res = sr.recognize(TEST_PATH)
    # print('\nPredict:\n', res)

