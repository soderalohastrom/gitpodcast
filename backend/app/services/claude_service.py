from anthropic import Anthropic
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import os

load_dotenv()

class MemoryStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    def __init__(self):
        super().__init__()
        self._audio_data = bytes()

    def write(self, audio_buffer: memoryview) -> int:
        self._audio_data += bytes(audio_buffer)
        return audio_buffer.nbytes

    def close(self):
        pass

    def get_audio_data(self) -> bytes:
         return self._audio_data


class ClaudeService:
    def __init__(self):
        self.default_client = Anthropic()
        # Load environment variables
        self.speech_key = os.environ.get("SPEECH_KEY")
        self.speech_region = os.environ.get("SPEECH_REGION")

    def call_claude_api(self, system_prompt: str, data: dict, api_key: str | None = None) -> str:
        """
        Makes an API call to Claude and returns the response.

        Args:
            system_prompt (str): The instruction/system prompt
            data (dict): Dictionary of variables to format into the user message
            api_key (str | None): Optional custom API key

        Returns:
            str: Claude's response text
        """
        # Create the user message with the data
        user_message = self._format_user_message(data)

        # Use custom client if API key provided, otherwise use default
        client = Anthropic(api_key=api_key) if api_key else self.default_client

        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ]
        )
        return message.content[0].text  # type: ignore

    # autopep8: off
    def _format_user_message(self, data: dict[str, str]) -> str:
        """Helper method to format the data into a user message"""
        parts = []
        for key, value in data.items():
            if key == 'file_tree':
                parts.append(f"<file_tree>\n{value}\n</file_tree>")
            elif key == 'readme':
                parts.append(f"<readme>\n{value}\n</readme>")
            elif key == 'explanation':
                parts.append(f"<explanation>\n{value}\n</explanation>")
            elif key == 'component_mapping':
                parts.append(f"<component_mapping>\n{value}\n</component_mapping>")
            elif key == 'instructions' and value != "":
                parts.append(f"<instructions>\n{value}\n</instructions>")
            elif key == 'diagram':
                parts.append(f"<diagram>\n{value}\n</diagram>")
            elif key == 'explanation':
                parts.append(f"<explanation>\n{value}\n</explanation>")
        return "\n\n".join(parts)
    # autopep8: on

    def count_tokens(self, prompt: str) -> int:
        """
        Counts the number of tokens in a prompt.

        Args:
            prompt (str): The prompt to count tokens for

        Returns:
            int: Number of input tokens
        """
        response = self.default_client.messages.count_tokens(
            model="claude-3-5-sonnet-latest",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return response.input_tokens

    def text_to_mp3(self, ssml_string: str) -> bytes | None:
        """
        Converts a string to an mp3 bytes object using Azure Text to Speech

        Args:
            ssml_string (str): Text to be converted to speech

        Returns:
            bytes | None: Returns mp3 bytes object, None if error
        """

        if not self.speech_key or not self.speech_region:
            return None
        print(self.speech_key, ssml_string)


        # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
        print("s1")
        # The neural multilingual voice can speak different languages based on the input text.
        speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'

        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)

        # # Creates a memory stream as the audio output stream instead of a file.
        # audio_config = speechsdk.audio.AudioOutputConfig(stream=speechsdk.audio.PushAudioOutputStream(speechsdk.audio.MemoryStreamCallback()), use_default_speaker=True)
        # speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Creates a memory stream as the audio output stream instead of a file.
        stream_callback = MemoryStreamCallback()
        audio_stream = speechsdk.audio.AudioOutputConfig(stream=speechsdk.audio.PushAudioOutputStream(stream_callback))

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_stream)

        result = speech_synthesizer.speak_ssml_async(ssml_string).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return stream_callback.get_audio_data()
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
            return b""
