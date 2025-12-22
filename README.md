# vip-rec

# Installation
```shell
conda create -n vip python=3.10
conda activate vip
```

Then install unitree_sdk2_python

```shell
pip install uv
```

Then go to the root of this project
```shell
uv pip install -e .
```

# Execution
On robot /home/unitree/workspace/services/airshow

Run zed_image_server.py

On laptop demo/zed_image_client_face_rec.py

Run zed_image_client_face_rec.py


# implementation
You can edit the greet function to make the robot say the content and do the gestures at the same time.
```Python
def greet(robot, name):
    if name == 'UNKNOWN':
        wav_path = robot.gen_wave('Hello, welcome to the airshow!')
        robot.play_wav(wav_path)
    else:
        wav_path = robot.gen_wave(f"Hello, {name}, welcome to the airshow!")
        robot.play_wav(wav_path)
    robot.wave_hand()
```