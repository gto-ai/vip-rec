import zmq
import json
import time

from util.redis_helper import Redis

ctx = zmq.Context.instance()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5557")

time.sleep(0.5)

while True:
    status = Redis.get('action_status')
    if status == 'idle':
        print(status)

        params = {
            "action": "wave_hand"
        }

        pub.send_string(json.dumps(params))
        time.sleep(1)