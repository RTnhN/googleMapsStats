#!/usr/bin/env python3
"""
Compare, dedupe-free, and report image view histories from CSVs,
combining series according to pairs.json.

Usage:
    python compare_and_report.py --data_folder Data --pairs pairs.json --output index.html

Requires:
    pip install matplotlib tqdm
"""

import os
import csv
import json
from collections import defaultdict
from datetime import datetime
import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor


def dict_merge(dict1, dict2):
    combined = {}
    for key in set(dict1) | set(dict2):
        v1 = dict1.get(key, "Unknown")
        v2 = dict2.get(key, "Unknown")
        combined[key] = v1 if v1 != "Unknown" else v2
    return combined


def process_csv(file_path):
    views_data = {}
    capture_data = {}
    with open(file_path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            url = row[0]
            views_data[url] = int(row[1])
            if len(row) == 3:
                capture_data[url] = row[2]
    return views_data, capture_data


def extract_timestamp(file_name):
    base = os.path.splitext(file_name)[0]
    parts = base.split("+")
    if len(parts) > 1:
        ts = parts[-1].replace("_", ":").replace("T", " ").replace("Z", "")
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
    return None


def combine_dictionaries(folder_path):
    combined = defaultdict(list)
    capture_dates = {}
    for fn in os.listdir(folder_path):
        if not fn.endswith(".csv"):
            continue
        ts = extract_timestamp(fn)
        if not ts:
            continue
        views, caps = process_csv(os.path.join(folder_path, fn))
        capture_dates = dict_merge(capture_dates, caps)
        for url, v in views.items():
            combined[url].append((ts, v))
    result = {}
    for url, lst in combined.items():
        lst.sort(key=lambda x: x[0])
        times, vals = zip(*lst)
        result[url] = (list(times), list(vals))
    return result, capture_dates


def merge_pairs(data, capture_dates, pairs):
    """
    For each gps_url in pairs, merge its series with the paired other_url,
    then remove the other_url entry.
    """
    for gps_url, other_url in pairs.items():
        t1, v1 = data.get(gps_url, ([], []))
        t2, v2 = data.get(other_url, ([], []))
        merged = sorted(zip(t1 + t2, v1 + v2), key=lambda x: x[0])
        if merged:
            times, vals = zip(*merged)
            data[gps_url] = (list(times), list(vals))
        else:
            data[gps_url] = ([], [])
        # merge capture dates
        d1 = capture_dates.get(gps_url, "Unknown")
        d2 = capture_dates.get(other_url, "Unknown")
        capture_dates[gps_url] = d1 if d1 != "Unknown" else d2
        # remove other_url
        data.pop(other_url, None)
        capture_dates.pop(other_url, None)
    return data, capture_dates


def plot_data(timestamps, views):
    fname = str(uuid.uuid4())
    fig, ax = plt.subplots()
    ax.plot(timestamps, views, marker=".")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Views")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(fname, format="svg")
    plt.close(fig)
    with open(fname, "r") as f:
        svg = f.read()
    os.remove(fname)
    return svg


def generate_html_report(data, capture_dates, output_html):
    with open(output_html, "w") as f:
        f.write("<html><body>\n<h1>Image Views Report</h1>\n")
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(plot_data, times, vals): url
                for url, (times, vals) in data.items()
            }
            for fut in tqdm(futures, total=len(futures), desc="Plotting"):
                url = futures[fut]
                svg = fut.result()
                cap = capture_dates.get(url, "Unknown")
                f.write(f"<b>Capture Date:</b> {cap}<br>\n")
                f.write('<div style="display:flex;align-items:center;">')
                f.write(
                    f'<div style="margin-right:20px;"><img src="{url}" width="300"></div>'
                )
                f.write("<div>" + svg + "</div></div>\n")
        f.write("</body></html>\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--data_folder", default="Data", help="Folder containing CSV files"
    )
    parser.add_argument(
        "--pairs", default="pairs.json", help="File containing pairing data"
    )
    parser.add_argument("--output", default="index.html", help="Output HTML file")
    args = parser.parse_args()

    data, caps = combine_dictionaries(args.data_folder)
    with open(args.pairs, "r") as f:
        pairs = json.load(f)
    data, caps = merge_pairs(data, caps, pairs)
    generate_html_report(data, caps, args.output)
    print(f"HTML report generated: {args.output}")
