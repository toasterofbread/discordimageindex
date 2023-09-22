import os

import imageindex
from server import Server
import os
from flask import Flask, redirect, request, abort
import threading
import firebase_admin
from firebase_admin import firestore, credentials
import asyncio

class MainServer(Server):
    def __init__(self, bot_token: str, images_channel_category: str, images_channel_prefix: str):
        super().__init__(bot_token, images_channel_category, images_channel_prefix)
        self.ready = False

    async def onReady(self):
        print("READY")
        self.loop = asyncio.get_event_loop()
        self.ready = True

    async def onNewImageAdded(self, image_id: str, image_url: str):
        imageindex.setImageUrl(db, image_id, image_url)

def isRemoteEnvironment():
    return os.getenv("REMOTE") == "1"

def getDb():
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

def getServer() -> Server:
    with open("keys.properties", "r") as f:
        bot_token = None
        images_channel_category = None
        images_channel_prefix = None

        for line in f.readlines():
            split = line.split("=", maxsplit = 1)
            match split[0]:
                case "DISCORD_BOT_TOKEN":
                    bot_token = split[1].strip().strip("\"")
                case "DISCORD_CUSTOM_IMAGES_CHANNEL_CATEGORY":
                    images_channel_category = split[1].strip().strip("\"")
                case "DISCORD_CUSTOM_IMAGES_CHANNEL_NAME_PREFIX":
                    images_channel_prefix = split[1].strip().strip("\"")

        return MainServer(bot_token, images_channel_category, images_channel_prefix)

app = Flask(__name__)
server = getServer()
db = getDb()

@app.route("/")
def index():
    return "Hello!"

@app.route("/getimages/<ids>")
def getImages(ids: str):
    ret = []
    for id in ids.split(","):
        ret.append(imageindex.findImageUrl(db, id) or "")
    return ",".join(ret)

rebuild_lock = asyncio.Lock()
async def startRebuild():
    async with rebuild_lock:
        await imageindex.rebuildIndex(db, server)

@app.route("/rebuild")
def rebuild():
    pw = os.getenv("pw", default = None)
    if pw is not None and request.args.get("pw") != pw:
        return abort(401, "pw incorrect or not provided")
    
    if not server.ready:
        return abort(503, "Server not ready")

    if rebuild_lock.locked():
        return "Already rebuilding", 202

    asyncio.run_coroutine_threadsafe(startRebuild(), loop = server.loop)
    return "Index rebuild started"

@app.route("/clear")
def clear():
    pw = os.getenv("pw", default = None)
    if pw is not None and request.args.get("pw") != pw:
        return abort(401, "pw incorrect or not provided")
    
    imageindex.clearIndex(db)

    return "Index cleared"

if __name__ == "__main__":
    flask_thread = threading.Thread(
        target = lambda: app.run(debug = False, host = "0.0.0.0", port = int(os.environ.get("PORT", 8081)))
    )
    flask_thread.start()

    server.runServer()
