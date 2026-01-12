import time
import zmq
import json
from pathlib import Path
from loguru import logger

from util.redis_helper import Redis
from util.g1_action import G1Action
from config import BASE


class ActionAgent:
    def __init__(self, **kwargs):
        self.robot = G1Action()
        self.action_ip = kwargs.get('action_ip', "127.0.0.1")

        ctx = zmq.Context.instance()
        self.action_sub = ctx.socket(zmq.SUB)
        self.action_sub.setsockopt(zmq.CONFLATE, 1)
        self.action_sub.connect(f"tcp://{self.action_ip}:5557")
        self.action_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.action_sub.setsockopt(zmq.RCVTIMEO, 1000)

        Redis.set('action_status', 'idle')

    def execute_action(self, action_name):
        Redis.set('action_status', 'busy')
        logger.info(action_name)

        if action_name == 'wave_hand':
            self.robot.wave_hand()
        elif action_name == 'heart':
            self.robot.heart()
        elif action_name == 'conversational_gesture':
            self.robot.conversational_gesture()
        else:
            pass

        Redis.set('action_status', 'idle')

    def run(self):
        logger.info('Action agent is running.')

        while True:
            try:
                msg = self.action_sub.recv_string()
            except zmq.Again:
                time.sleep(0.1)
                continue

            data = json.loads(msg)
            if 'action' in data:
                action_name = data['action']
                self.execute_action(action_name)


def main():
    agent = ActionAgent()
    agent.run()


if __name__ == '__main__':
    main()
