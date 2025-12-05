import asyncio
import json
import ssl
import websockets
from pathlib import Path

from config import BASE

ALERT_MESSAGE = {
    'idEventVap': 'fe1e3831-66d9-4bd1-8cfa-360e7dd1068a',
    'idCameraRef': '6120f1fe-9af6-4389-975a-1d0b58c206e3',
    'cameraName': 'AirShow',
    'alertType': 'poi',
    'textSearchField': 'Ruofei',
    'verificationStatus': 'PENDING',
    'confidence': 0.7809642553329468,
    'idEnrolmentRef': 'd39b2ecb-3949-4424-8828-74f109e11c47',
    'enrolmentName': 'Ruofei',
    'imageUrlCrop': 'https://minio.fake/crop.jpg',
    'imageUrlScene': 'https://minio.fake/scene.jpg',
    'imageUrlEnrollment': 'https://minio.fake/enrol.jpg',
    'dateTimeVapDetected': '2025-12-04T09:12:46.069Z',
    'dateTimeVaDetected': '2025-12-04T09:12:45.629Z',
    'cameraAddress': 'UNASSIGNED',
    'watchlistType': 'BLACKLIST',
    'accessType': 'UNAUTHORIZED'
}

connected_clients = set()


async def client_handler(websocket):
    connected_clients.add(websocket)
    print("Client connected")

    try:
        await asyncio.Future()  # keep alive
    except:
        pass
    finally:
        connected_clients.remove(websocket)
        print("Client disconnected")


async def broadcaster():
    while True:
        if connected_clients:
            msg = json.dumps(ALERT_MESSAGE)
            print(f"Broadcasting to {len(connected_clients)} client(s)")

            await asyncio.gather(*[
                ws.send(msg) for ws in connected_clients
            ], return_exceptions=True)

        await asyncio.sleep(5)


async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        str(Path(BASE, "credential", "server_vap_backend.crt")),
        str(Path(BASE, "credential", "server_vap_backend.key"))
    )

    async with websockets.serve(
            client_handler,
            host="0.0.0.0",
            port=8094,
            ssl=ssl_context
    ):
        print("WSS server running at wss://0.0.0.0:8094")
        await broadcaster()


if __name__ == "__main__":
    asyncio.run(main())
