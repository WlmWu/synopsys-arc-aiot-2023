import logging
from flask import abort
from .config import GOOGLE_API_KEY, APP_AUTH_TOKEN
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import vision
from google.api_core.client_options import ClientOptions

clientOptions = ClientOptions() if GOOGLE_API_KEY is None else ClientOptions(api_key=GOOGLE_API_KEY)


def parse_token_from_auth_header(auth_header):
    try:
        if isinstance(auth_header, str):
            auth_token = auth_header.strip().split(" ")[-1]
            logging.info(f'parse_token_from_auth_header;SUCCESS;AUTH_HEADER;{auth_header};TOKEN;{auth_token}')
            return auth_token
        else:
            logging.info(f'parse_token_from_auth_header;None;AUTH_HEADER;{auth_header};TOKEN;{None}')
            return None
    except BaseException as err:
        logging.warning(f'parse_token_from_auth_header;error;{err}')
        return None


def check_auth_token_is_valid(token) -> bool:
    if token is None or token != APP_AUTH_TOKEN:
        logging.warning(f'check_auth_token_is_valid;INVALID;TOKEN;{token}')
        abort(401, "The server could not verify that you are authorized to access the URL requested.")

    logging.info(f'check_auth_token_is_valid;VALID;TOKEN;{token}')
    return True


def detect_text(content: bytes) -> list:
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient(client_options=clientOptions)

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        abort(400, response.error.message)

    data = []
    for text in response.text_annotations:
        data.append({
            'description': text.description,
            'vertices': [{'x': vertex.x, 'y': vertex.y} for vertex in text.bounding_poly.vertices]
        })

    return data


def text_to_speech(text: str) -> bytes:
    # Instantiates a client
    client = texttospeech.TextToSpeechClient(client_options=clientOptions)

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(language_code="zh-TW", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    # The response's audio_content is binary.
    return response.audio_content


def speech_to_text(content: bytes) -> list:
    # Instantiates a client
    client = speech.SpeechClient(client_options=clientOptions)

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, language_code="zh-TW")

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    data = []
    for result in response.results:
        for alt in result.alternatives:
            data.append({'transcript': alt.transcript, 'confidence': alt.confidence})

    return data
