from flask import Flask, jsonify, render_template
from flask_cors import CORS
from event_stream_with_models import EVENT_STREAM, simulation_loop
import threading

app = Flask(__name__, template_folder="templates")
CORS(app)

@app.route("/")
def home():
    return render_template("map.html")

@app.route("/events")
def events():
    return jsonify(EVENT_STREAM[-50:])

if __name__ == "__main__":
    threading.Thread(target=simulation_loop, daemon=True).start()
    app.run(port=5500, debug=False)
