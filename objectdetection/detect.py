import base64
import socketio

from openai import OpenAI
import os
from dotenv import load_dotenv
from cv2 import VideoCapture, imshow, imwrite
import numpy as np

load_dotenv()

# only called when flight program finishes
# wait some amt of time(for demo)
# seat value determined outside of this program.

sio = socketio.Client()
SOCKET_IP = os.getenv("SOCKET_IP") or "http://localhost:3000"

@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.event
def syncData(data):
    print("received sync data: ", data)
    if "READY" in data:
        run_detection()


@sio.event
def disconnect():
    print("I'm disconnected!")


def run_detection():
    # take photo
    cam_port = 0
    cam = VideoCapture(cam_port)
    result, image = cam.read()
    a = np.double(image)
    b = a + 15
    img = np.uint8(b)
    if result:
        # imshow("Chair", img) # debug
        imwrite("Chair.jpg", img)
    else:
        print("No image detected. Please! try again")

    res = detect_items()
    print(res)

    (firstWord, rest) = res.split(maxsplit=1)
    if firstWord != "No":
        # websocket the item back (result)
        resp = "A05 " + rest
        sio.emit("syncData", resp.lower())
    else:
        resp = "A05" + " No"
        sio.emit("syncData", resp.lower())


def detect_items():
    key = os.environ["OPENAI_API_KEY"]
    client = OpenAI(api_key=key)
    with open("Chair.jpg", "rb") as image_file:
        im_b64 = base64.b64encode(image_file.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Assume you are checking if someone left an item on an airplane seat. Yes or No, "
                        "is there any physical object in the chair in the center of the photo? Exclude shadows. "
                        "If yes, what object is in the chair? Just give the name of the object without a full "
                        "sentence or period at the end. If you cannot understand the photo, type No.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpg;base64,{im_b64}",
                            "detail": "low",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print(SOCKET_IP)
    sio.connect(SOCKET_IP, transports=["websocket", "polling"])
    sio.wait()

