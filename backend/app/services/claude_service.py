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
        # ssml_string = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     <prosody pitch="medium">Welcome to Next Gen Innovators!</prosody>
        #                     <break time="500ms" />
        #                     I’m your host, Ava, and today we’re diving into an exciting topic: how students can embark on their entrepreneurial journey right from college.
        #                     <break time="700ms" />
        #                     Joining us is Arun Sharma, a seasoned entrepreneur with over two decades of experience and a passion for mentoring young innovators.
        #                     <break time="500ms" />
        #                     Arun, it’s a pleasure to have you here.
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     <prosody rate="medium">Thank you, Ava.</prosody>
        #                     <break time="300ms" />
        #                     It’s great to be here. I’m excited to talk about how students can channel their creativity and energy into building impactful ventures.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     Let’s start with the big question:
        #                     <break time="300ms" />
        #                     Why do you think college is a good time for students to explore entrepreneurship?
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     That’s a fantastic question.
        #                     <break time="300ms" />
        #                     College is a unique phase where students have access to an incredible ecosystem—peers from diverse disciplines, supportive faculty, and often, institutional resources like startup incubators or entrepreneurship cells.
        #                     <break time="500ms" />
        #                     Plus, students are at a stage where they can take calculated risks without the heavy financial or family responsibilities that might come later in life.
        #                     <break time="500ms" />
        #                     It’s the perfect playground for experimenting and learning.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     That’s a great way to frame it!
        #                     <break time="300ms" />
        #                     But what about the practical challenges? Many students might think they lack the funds, connections, or even time to start something meaningful.
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     Absolutely, those concerns are valid.
        #                     <break time="300ms" />
        #                     But let’s break them down. For funding, students can explore grants, pitch competitions, or crowdfunding platforms.
        #                     <break time="500ms" />
        #                     Connections? Start by tapping into your college’s alumni network or attending local startup events.
        #                     <break time="500ms" />
        #                     And as for time, it’s about prioritization. Starting small with side projects and dedicating even a couple of hours a week can make a huge difference.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     That’s actionable advice.
        #                     <break time="300ms" />
        #                     Speaking of starting small, what types of ventures or projects do you recommend for students?
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     I’d suggest students start with problems they’re personally passionate about or face themselves.
        #                     <break time="300ms" />
        #                     For instance, if campus dining is inefficient, maybe there’s an app idea in there.
        #                     <break time="500ms" />
        #                     Or if you’re passionate about sustainability, think about creating eco-friendly products or services.
        #                     <break time="500ms" />
        #                     Begin with a minimum viable product (MVP) to test the waters and refine your idea based on real feedback.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     I love that—solving problems you’re connected to makes the journey more meaningful.
        #                     <break time="300ms" />
        #                     What about building a team? That’s often cited as a critical factor in a startup’s success.
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     You’re spot on, Ava.
        #                     <break time="300ms" />
        #                     A team can make or break a venture. In college, you have the advantage of being surrounded by talented peers.
        #                     <break time="500ms" />
        #                     Look for people who share your vision but bring complementary skills. If you’re great at coding, partner with someone strong in marketing or design.
        #                     <break time="500ms" />
        #                     Communication and trust are key—find people you genuinely enjoy working with.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     It sounds like collaboration is as much about chemistry as it is about skills.
        #                     <break time="300ms" />
        #                     Once students have their idea and team in place, how should they navigate the launch phase?
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     Start by validating your idea. Conduct surveys, talk to potential users, and gather as much feedback as possible.
        #                     <break time="500ms" />
        #                     Create a basic version of your product or service and test it with a small audience.
        #                     <break time="500ms" />
        #                     Use free or affordable tools to build your first iteration—there’s no need for perfection at this stage.
        #                     <break time="500ms" />
        #                     Once you’ve proven there’s demand, you can scale gradually.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     This approach makes entrepreneurship feel a lot more accessible.
        #                     <break time="300ms" />
        #                     But what about the emotional side? How can students stay resilient when they hit inevitable roadblocks?
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     Resilience is a muscle that grows with experience.
        #                     <break time="300ms" />
        #                     The first thing I’d say is to reframe failures as learning opportunities. Every mistake you make teaches you something invaluable.
        #                     <break time="500ms" />
        #                     Secondly, surround yourself with a supportive community—friends, mentors, or even online forums.
        #                     <break time="500ms" />
        #                     Lastly, keep your long-term vision in mind. It’ll help you push through tough times.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     Wise words, Arun.
        #                     <break time="300ms" />
        #                     Before we wrap up, do you have a final message for students who’re curious but hesitant about diving into entrepreneurship?
        #                 </voice>

        #                 <voice name="en-US-AndrewMultilingualNeural">
        #                     Absolutely. My message is: Just start.
        #                     <break time="300ms" />
        #                     You don’t have to know everything or have a perfect plan.
        #                     <break time="300ms" />
        #                     The most important step is the first one—whether that’s brainstorming ideas, attending a workshop, or reaching out to potential co-founders.
        #                     <break time="500ms" />
        #                     Every small step compounds over time.
        #                 </voice>

        #                 <voice name="en-US-AvaMultilingualNeural">
        #                     Thank you, Arun, for sharing your insights and practical tips.
        #                     <break time="300ms" />
        #                     I’m sure our listeners are feeling inspired to take that first step.
        #                     <break time="300ms" />
        #                     To everyone tuning in, remember: entrepreneurship isn’t just about building a business; it’s about solving problems, learning, and growing.
        #                 </voice>
        #             </speak>
        #             """
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
