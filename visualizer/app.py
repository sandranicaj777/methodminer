import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import redis
import threading
import time



app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Connect to Redis
try:
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to Redis successfully")
except redis.exceptions.ConnectionError:
    print("Failed to connect to Redis")
    r = None

@app.route("/")
def index():
    return render_template("index.html")

# Background thread, listens for new words
def redis_listener():
    if not r:
        print("Redis not connected; listener aborted")
        return
    pubsub = r.pubsub()
    pubsub.subscribe("word_stream")  
    print("Subscribed to Redis channel: word_stream")
    for message in pubsub.listen():
        if message["type"] == "message":
            word = message["data"]
            socketio.emit("new_word", {"word": word})
            print("New word received:", word)

# Start listener thread
threading.Thread(target=redis_listener, daemon=True).start()

if __name__ == "__main__":
    print("Starting Visualizer server...")
    socketio.run(app, host="0.0.0.0", port=5050, debug=True, use_reloader=False)


