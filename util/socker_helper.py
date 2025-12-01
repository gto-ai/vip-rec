import asyncio
import json
import ssl
import websockets

WS_URL = "wss://backend.vap:8094/vap-face-alerts-v3"

# ----------------------------------------------------------
# Create SSL context that ignores certificate verification
# (Required because backend.vap uses internal cert)
# ----------------------------------------------------------
def create_unverified_ssl():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


# ----------------------------------------------------------
# Parse FR alert JSON message and extract useful fields
# ----------------------------------------------------------
def process_fr_alert(data):
    """
    Extract useful fields from FR alert message.
    """

    useful = {
        "idEventVap": data.get("idEventVap"),
        "cameraName": data.get("cameraName"),
        "confidence": data.get("confidence"),
        "enrolmentName": data.get("enrolmentName"),
        "imageUrlCrop": data.get("imageUrlCrop"),
        "imageUrlScene": data.get("imageUrlScene"),
        "imageUrlEnrollment": data.get("imageUrlEnrollment"),
        "dateTimeVaDetected": data.get("dateTimeVaDetected")
    }

    print("\n🔔 NEW FR ALERT RECEIVED:")
    for k, v in useful.items():
        print(f"{k}: {v}")


# ----------------------------------------------------------
# Connect & Listen Loop
# ----------------------------------------------------------
async def listen_fr_alerts():
    ssl_context = create_unverified_ssl()

    while True:
        try:
            print(f"Connecting to {WS_URL} ...")

            async with websockets.connect(
                WS_URL,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=20,
                max_size=10 * 1024 * 1024
            ) as ws:

                print("✅ Connected! Listening for FR alerts...\n")

                async for message in ws:
                    try:
                        data = json.loads(message)
                        process_fr_alert(data)

                    except Exception as e:
                        print(f"⚠️ Failed to process message: {e}")
                        print("Raw message:", message)

        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            print("Reconnecting in 5 seconds...\n")
            await asyncio.sleep(5)


# ----------------------------------------------------------
# Entry point
# ----------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(listen_fr_alerts())
