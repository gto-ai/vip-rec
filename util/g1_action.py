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
from loguru import logger


class G1Action:
    def __init__(self, **kwargs):
        network_interface = IPHelper.get_network_interface('192.168.123.*')
        ChannelFactoryInitialize(0, network_interface)

        self.arm_client = G1ArmActionClient()
        self.arm_client.SetTimeout(10.0)
        self.arm_client.Init()

        self.state = 'idle'

        self.username = IPHelper.get_username()

    def wave_hand(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("face wave"))
        self.state = 'idle'

    def heart(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("heart"))
        time.sleep(2)
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'

    def clap(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("clap"))
        self.state = 'idle'

    def high_five(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("high five"))
        time.sleep(0.5)
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'

    def right_hand_up(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("right hand up"))
        time.sleep(2)
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'

    def hands_up(self):
        self.state = 'busy'
        self.arm_client.ExecuteAction(action_map.get("hands up"))
        time.sleep(1)
        self.arm_client.ExecuteAction(action_map.get("release arm"))
        self.state = 'idle'

    def conversation_gesture(self):
        self.state = 'busy'
        script = str(Path(BASE, 'util', 'action', 'run_conversation_gesture.py'))
        subprocess.run([sys.executable, script], check=True)
        self.state = 'idle'

    def neutral_gesture(self):
        self.state = 'busy'
        script = str(Path(BASE, 'util', 'action', 'run_neutral_gesture.py'))
        subprocess.run([sys.executable, script], check=True)
        self.state = 'idle'

    def open_gesture(self):
        self.state = 'busy'
        script = str(Path(BASE, 'util', 'action', 'run_open_gesture.py'))
        subprocess.run([sys.executable, script], check=True)
        self.state = 'idle'



def main():
    robot = G1Action()
    robot.conversational_gesture()


if __name__ == "__main__":
    main()
