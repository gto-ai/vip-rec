import time
import subprocess
from pathlib import Path
import sys
from config import BASE
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map
from util.wav import read_wav, play_pcm_stream
from util.edgetts_helper import EdgeTTS
from util.ip_helper import IPHelper



class G1Action:
    def __init__(self, **kwargs):
        network_interface = IPHelper.get_network_interface('192.168.123.*')
        ChannelFactoryInitialize(0, network_interface)

        self.arm_client = G1ArmActionClient()
        self.arm_client.SetTimeout(10.0)
        self.arm_client.Init()

        self.state = 'idle'

        self.username = IPHelper.get_username()
        self.python_bin = '/home/rfouyang/anaconda3/envs/vip/bin/python'

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

    def conversational_gesture(self):
        script = str(Path(BASE, 'util', 'action', 'conversational_gesture.py'))
        subprocess.run([self.python_bin, script], check=True)


def main():
    robot = G1Action()
    robot.conversational_gesture()


if __name__ == "__main__":
    main()
