from flask import Flask
import time
app = Flask(__name__)


@app.route('/hc')
def hc():
    return "ok", 200


@app.route('/ok')
def ok():
    return "ok", 200


@app.route('/ng')
def ng():
    return "ng", 500


@app.route('/heavy')
def heavy():
    time.sleep(60)
    return "ok", 200


if __name__ == "__main__":
    app.run(debug=True)
