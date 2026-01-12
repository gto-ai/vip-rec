import zmq
import json
import time

from util.redis_helper import Redis

ctx = zmq.Context.instance()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5556")

time.sleep(0.5)

while True:
    status = Redis.get('audio_status')
    if status == 'idle':
        print(status)

        params = {
            "name": "Ruofei",
            "article": "article_1"
        }

        pub.send_string(json.dumps(params))
        time.sleep(1)