import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
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
    lang = request.args.get("lang", "all")
    if not r:
        return jsonify({})
    data = r.hgetall(f"word_counts:{lang}")
    sorted_data = dict(sorted(data.items(), key=lambda x: int(x[1]), reverse=True))
    return jsonify(sorted_data)

@app.route("/api/analytics")
def analytics():
    """Top 5 words per language"""
    result = {}
    for lang in ["python", "java", "all"]:
        data = r.hgetall(f"word_counts:{lang}")
        top5 = sorted(data.items(), key=lambda x: int(x[1]), reverse=True)[:5]
        result[lang] = top5
    result["last_repo"] = r.get("last_repo")
    return jsonify(result)

def redis_listener():
    if not r:
        print("Redis not connected; listener aborted")
        return

    pubsub = r.pubsub()
    pubsub.subscribe("word_stream")
    print("Subscribed to Redis channel: word_stream")

    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                repo, lang, word = message["data"].split("|")
            except ValueError:
                repo, lang, word = "unknown_repo", "unknown_lang", message["data"]

            r.hincrby(f"word_counts:{lang}", word, 1)
            r.hincrby("word_counts:all", word, 1)
            r.set("last_repo", repo)

            socketio.emit("new_word", {"word": word, "lang": lang, "repo": repo})
            print(f"[{lang}] {repo}: {word}")

threading.Thread(target=redis_listener, daemon=True).start()

if __name__ == "__main__":
    print("Starting Visualizer server on port 5050...")
    socketio.run(app, host="0.0.0.0", port=5050)
