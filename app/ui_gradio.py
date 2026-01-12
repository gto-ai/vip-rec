import json

import gradio as gr
from util.redis_helper import Redis

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


def read_status():
    info = {
        "vip": Redis.get("vip"),
        "name": Redis.get("name"),
        "action_status": Redis.get("action_status"),
        "audio_status": Redis.get("audio_status"),
    }

    if info['vip'] is None:
        info['vip'] = ""

    return (json.dumps(info['vip']), json.dumps(info['name']),
            json.dumps(info['action_status']), json.dumps(info['audio_status']))


def fill_vip_name(selected):
    return selected


def turn_on_vip(vip_name):
    if not vip_name:
        return "❌ No VIP selected"

    Redis.set("vip", {"name": vip_name,"status": "on"})
    return f"✅ VIP {vip_name} turned ON"


def turn_off_vip():
    Redis.set("vip", {"status": "off"})
    return "⛔ VIP turned OFF"


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
        refresh = gr.Button("🔄 Refresh")

    refresh.click(
        fn=read_status,
        outputs=[vip, name, action_status, audio_status],
    )

    # ⏱ auto refresh every 1s
    timer = gr.Timer(2)
    timer.tick(
        fn=read_status,
        outputs=[vip, name, action_status, audio_status],
    )

    gr.Markdown("## 👑 VIP Selector")

    with gr.Row():
        with gr.Column(scale=1):
            vip_list = gr.Radio(
                choices=VIP_NAMES,
                label="VIP List",
            )

        with gr.Column(scale=1):
            vip_name = gr.Textbox(
                label="VIP Name",
                placeholder="Click a VIP from the list",
            )

    vip_list.change(
        fn=fill_vip_name,
        inputs=vip_list,
        outputs=vip_name,
    )

    with gr.Row():
        turn_on_btn = gr.Button("🟢 Turn ON VIP", variant="primary")
        turn_off_btn = gr.Button("🔴 Turn OFF VIP")

    status_msg = gr.Textbox(
        label="Status",
        interactive=False,
    )

    turn_on_btn.click(
        fn=turn_on_vip,
        inputs=vip_name,
        outputs=status_msg,
    )

    turn_off_btn.click(
        fn=turn_off_vip,
        outputs=status_msg,
    )

if __name__ == "__main__":
    demo.launch()
