import time
from enum import IntEnum

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map


class Language(IntEnum):
    Chinese = 0
    English = 1


class G1:
    def __init__(self, **kwargs):
        network_interface = kwargs.get('network_interface', 'enp108s0')
        ChannelFactoryInitialize(0, network_interface)

        self.audio_client = AudioClient()
        self.audio_client.SetTimeout(10.0)
        self.audio_client.Init()

        self.audio_client.SetVolume(90)

        self.arm_client = G1ArmActionClient()
        self.arm_client.SetTimeout(10.0)
        self.arm_client.Init()

        self.state = 'idle'

    def say(self, text, **kwargs):
        # 0: Chinese, 1: English
        language = kwargs.get('language', Language.English)
        self.audio_client.TtsMaker(text, language)

    def wave_hand(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("high wave"))
        self.state = 'idle'

    def heart(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("heart"))
        time.sleep(2)
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'

    def release_arm(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'


if __name__ == "__main__":
    robot = G1()
    robot.say('hello, nice to meet you in the airshow')
    # robot.wave_hand()
    robot.heart()
