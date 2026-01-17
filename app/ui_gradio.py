import json
import zmq
from loguru import logger
import gradio as gr
from util.redis_helper import Redis

# variables
# vip: {status: on/off, name: XXX, mode: manual/auto}
# name: name to pronouce
# action_status
# audio_status


VIP_NAMES = [
    "Prime Minister Wong",
    "Doctor Lee",
    "Kai Xin",
    "Mister Xiong",
    "Ruofei",
    "Yechao",
    "Pengfei",
    "Karthee"
]

ctx = zmq.Context.instance()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://127.0.0.1:5558")


def read_status():
    info = {
        "vip": Redis.get("vip"),
        "name": Redis.get("name"),
        "action_status": Redis.get("action_status"),
        "audio_status": Redis.get("audio_status"),
    }

    if info['vip'] is None:
        info['vip'] = {'status': 'off', 'name': "", "mode": "auto"}
        Redis.set("vip", info['vip'])

    return (
        json.dumps(info['vip']), json.dumps(info['name']),
        json.dumps(info['action_status']), json.dumps(info['audio_status'])
    )


def select_vip_name(selected):
    if selected is not None and len(selected) > 0:
        vip_info = Redis.get("vip")
        vip_info['name'] = selected
        Redis.set("vip", vip_info)
    return [selected, gr.update(interactive=True)]


def on_vip_toggle(checkbox_status):
    vip_info = Redis.get("vip")
    if vip_info['name'] == "":
        logger.error("vip name can't be empty")
        return gr.update(interactive=False)

    if checkbox_status is True:
        vip_info['status'] = "on"
        Redis.set("vip", vip_info)
        return gr.update(interactive=True)
    else:
        vip_info['status'] = "off"
        Redis.set("vip", vip_info)
        return gr.update(interactive=False)


def on_mode_toggle(checkbox_status):
    vip_info = Redis.get("vip")
    if vip_info['status'] == "off":
        return gr.update(interactive=False)

    if checkbox_status is True:
        vip_info['mode'] = "manual"
        Redis.set("vip", vip_info)
        return gr.update(interactive=True)

    else:
        vip_info['mode'] = "auto"
        Redis.set("vip", vip_info)
        return gr.update(interactive=False)


def on_trigger():
    status = Redis.get('audio_status')
    vip_info = Redis.get('vip')

    if status == 'idle':
        logger.info('Trigger audio')

        params = {
            "name": vip_info['name'],
            "article": "article_1"
        }

        pub.send_string(json.dumps(params))


with gr.Blocks(title="Redis Status Monitor") as demo:
    gr.Markdown("## 🔎 Redis Status Monitor")
    with gr.Row():
        with gr.Column(scale=1):
            vip = gr.JSON(label="vip")
            name = gr.JSON(label="name")
        with gr.Column(scale=1):
            action_status = gr.JSON(label="action_status")
            audio_status = gr.JSON(label="audio_status")
    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh")

    refresh_btn.click(fn=read_status,outputs=[vip, name, action_status, audio_status])
    timer = gr.Timer(1)
    timer.tick(fn=read_status, outputs=[vip, name, action_status, audio_status])

    gr.Markdown("## 👑 VIP Selector")
    with gr.Row():
        with gr.Column(scale=1):
            vip_list = gr.Radio(choices=VIP_NAMES,label="VIP List")
        with gr.Column(scale=1):
            vip_name = gr.Textbox(label="VIP Name", placeholder="Click a VIP from the list")
    with gr.Row():
        vip_toggle = gr.Checkbox(label="Enable VIP", interactive=False, value=False)
        mode_toggle = gr.Checkbox(label="Enable Mode", interactive=False, value=False)
        trigger_btn = gr.Button("Manual Trigger", interactive=False)

    vip_list.change(
        fn=select_vip_name,
        inputs=vip_list,
        outputs=[vip_name, vip_toggle],
    )

    vip_toggle.change(
        fn=on_vip_toggle,
        inputs=vip_toggle,
        outputs=mode_toggle
    )

    mode_toggle.change(
        fn=on_mode_toggle,
        inputs=mode_toggle,
        outputs=trigger_btn,
    )

    trigger_btn.click(
        fn=on_trigger,
        inputs=None,
        outputs=None
    )

if __name__ == "__main__":
    demo.launch()
