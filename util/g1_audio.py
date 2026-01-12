import time
from enum import IntEnum
import asyncio

from config import BASE
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map
from util.wav import read_wav, play_pcm_stream
from util.edgetts_helper import EdgeTTS
from util.ip_helper import IPHelper


class Language(IntEnum):
    Chinese = 0
    English = 1


class G1Audio:
    def __init__(self, **kwargs):
        network_interface = IPHelper.get_network_interface('192.168.123.*')
        ChannelFactoryInitialize(0, network_interface)

        self.audio_client = AudioClient()
        self.audio_client.SetTimeout(10.0)
        self.audio_client.Init()

        self.audio_client.SetVolume(90)

        self.tts = EdgeTTS()

        self.state = 'idle'

    def say(self, text, **kwargs):
        # 0: Chinese, 1: English
        language = kwargs.get('language', Language.English)
        self.audio_client.TtsMaker(text, language)

    def play_wav(self, wav_path):
        pcm_bytes, sample_rate, num_channels, is_ok = read_wav(wav_path)

        if not is_ok or sample_rate != 16000 or num_channels != 1:
            print("[ERROR] Failed to read WAV file or unsupported format (must be 16kHz mono)")
            return

        # play
        play_pcm_stream(self.audio_client, pcm_bytes, "example")

        # wait until playback finishes
        duration_sec = len(pcm_bytes) / (16000*3)  # mono int16
        time.sleep(duration_sec + 0.1)

        # now it is safe to stop
        self.audio_client.PlayStop("example")

    def gen_wave(self, text):
        wav_path = asyncio.run(self.tts.speak(text))
        return wav_path

    def greet(self, name):
        if name == 'UNKNOWN':
            wav_path = self.gen_wave('Hello, welcome to the airshow!')
            self.play_wav(wav_path)
        else:
            wav_path = self.gen_wave(f"Hello, {name}, welcome to the airshow!")
            self.play_wav(wav_path)


if __name__ == "__main__":
    robot = G1Audio()
    robot.play_wav('/home/rfouyang/workspace/services/vip-rec/data/article_1/article_1_000.wav')