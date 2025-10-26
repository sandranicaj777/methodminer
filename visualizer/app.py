import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import redis
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

try:
    r = redis.Redis(host="redis_service", port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to Redis successfully")
except redis.exceptions.ConnectionError:
    print("Failed to connect to Redis")
    r = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/words")
def get_words():
    """Return persisted word counts"""
    if not r:
        return jsonify({})
    data = r.hgetall("word_counts")
    sorted_data = dict(sorted(data.items(), key=lambda x: int(x[1]), reverse=True))
    return jsonify(sorted_data)


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
            r.hincrby("word_counts", word, 1)
            socketio.emit("new_word", {"word": word})
            print(f"New word: {word}")

threading.Thread(target=redis_listener, daemon=True).start()

if __name__ == "__main__":
    print("Starting Visualizer server on port 5050...")
    socketio.run(app, host="0.0.0.0", port=5050)
