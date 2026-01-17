import time
import zmq
import json
from pathlib import Path
from loguru import logger

from util.redis_helper import Redis
from util.g1_audio import G1Audio
from config import BASE


class TTSAgent:
    def __init__(self, **kwargs):
        self.g1_audio = G1Audio()
        self.audio_ip = kwargs.get('audio_ip', "127.0.0.1")
        self.action_ip = kwargs.get('action_ip', "127.0.0.1")

        ctx = zmq.Context.instance()
        self.audio_sub = ctx.socket(zmq.SUB)
        self.audio_sub.setsockopt(zmq.CONFLATE, 1)
        self.audio_sub.connect(f"tcp://{self.audio_ip}:5556")
        self.audio_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.audio_sub.setsockopt(zmq.RCVTIMEO, 1000)

        self.audio_sub2 = ctx.socket(zmq.SUB)
        self.audio_sub2.setsockopt(zmq.CONFLATE, 1)
        self.audio_sub2.connect(f"tcp://{self.audio_ip}:5558")
        self.audio_sub2.setsockopt_string(zmq.SUBSCRIBE, "")
        self.audio_sub2.setsockopt(zmq.RCVTIMEO, 1000)

        with Path(BASE, 'data', 'articles.json').open() as f:
            self.dict_info = json.loads(f.read())

        Redis.set('audio_status', 'idle')

        self.action_pub = ctx.socket(zmq.PUB)
        self.action_pub.bind(f"tcp://{self.action_ip}:5557")

    def read_article(self, article_id):

        for line in self.dict_info[article_id]:
            action = line['action']
            audio_path = line['audio']

            if action != "":
                action_status = Redis.get('action_status')
                if action_status is not None and action_status == 'idle':
                    params = {"action": action}
                    self.action_pub.send_string(json.dumps(params))
                    logger.info(action)

            self.g1_audio.play_wav(audio_path)
            logger.info(audio_path)

    def handle_message(self, msg):
        data = json.loads(msg)

        Redis.set('audio_status', 'busy')

        if 'article' in data:
            vip_info = Redis.get('vip')
            if vip_info is None or vip_info['status'] == 'off':
                name = data['name']
                Redis.set('name', name)
                self.g1_audio.greet(name)
                logger.info(name)
                Redis.set('name', "")

                article_id = data['article']
                # self.read_article(article_id)
            else:
                if 'name' in vip_info:
                    name = vip_info['name']
                    Redis.set('name', name)
                    self.g1_audio.greet(name)
                    logger.warning(name)

                    article_id = data['article']
                    # self.read_article(article_id)
                    Redis.set('name', "")

        Redis.set('audio_status', 'idle')

    def run(self):
        logger.info('TTS agent is running.')

        poller = zmq.Poller()
        poller.register(self.audio_sub, zmq.POLLIN)
        poller.register(self.audio_sub2, zmq.POLLIN)

        while True:
            try:
                events = dict(poller.poll(timeout=1000))  # 1s timeout
            except KeyboardInterrupt:
                break

            if self.audio_sub in events:
                msg = self.audio_sub.recv_string()
                self.handle_message(msg)

            if self.audio_sub2 in events:
                msg = self.audio_sub2.recv_string()
                self.handle_message(msg)


def main():
    agent = TTSAgent()
    agent.run()
    # agent.read_article('article_1')


if __name__ == '__main__':
    main()
