from flask import Flask, render_template, jsonify, send_file
import json
import os
import csv

app = Flask(__name__)


def get_image_urls():
    data_path = os.path.join(os.path.dirname(__file__), "..", "Data")
    urls = set()
    for fn in os.listdir(data_path):
        if not fn.endswith(".csv"):
            continue
        with open(os.path.join(data_path, fn), "r", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 2:
                    continue
                url = row[0]
                urls.add(url)
    return list(urls)


def load_urls():
    gps = []
    other = []
    urls = get_image_urls()
    for url in urls:
        if "/gps" in url:
            gps.append(url)
        else:
            other.append(url)
    return gps, other


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/images")
def images():
    gps, other = load_urls()
    return jsonify({"gps": gps, "other": other})


if __name__ == "__main__":
    app.run(debug=True)
