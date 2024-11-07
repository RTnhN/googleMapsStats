import os
import csv
from collections import defaultdict
from datetime import datetime
import matplotlib
import uuid

matplotlib.use("Agg")  # Use the 'Agg' backend for background plot generation
import matplotlib.pyplot as plt

from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor


def dict_merge(dict1, dict2):
    combined = {}
    for key in set(dict1) | set(dict2):
        value1 = dict1.get(key, "Unknown")
        value2 = dict2.get(key, "Unknown")

        if value1 != "Unknown":
            combined[key] = value1
        elif value2 != "Unknown":
            combined[key] = value2
        else:
            combined[key] = "Unknown"
    return combined


def process_csv(file_path):
    views_data = {}
    capture_data = {}

    with open(file_path, mode="r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            if len(row) < 2:
                continue  # Skip invalid rows
            url = row[0]
            views_data[url] = int(row[1])
            if len(row) == 3:
                capture_data[url] = row[2]
    return views_data, capture_data


def extract_timestamp(file_name):
    file_name_no_ext = os.path.splitext(file_name)[0]
    parts = file_name_no_ext.split("+")
    if len(parts) > 1:
        timestamp_str = parts[-1]
        timestamp_str = (
            timestamp_str.replace("_", ":").replace("T", " ").replace("Z", "")
        )
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    return None


def combine_dictionaries(folder_path):
    combined_dict = defaultdict(list)
    capture_date_dict = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            timestamp = extract_timestamp(file_name)
            if timestamp:
                file_path = os.path.join(folder_path, file_name)
                views_data, capture_data = process_csv(file_path)
                capture_date_dict = dict_merge(capture_date_dict, capture_data)
                for url, views in views_data.items():
                    combined_dict[url].append((timestamp, views))
    for url in combined_dict:
        combined_dict[url].sort(key=lambda x: x[0])
    final_dict = {
        url: (list(zip(*views_list))[0], [views for _, views in views_list])
        for url, views_list in combined_dict.items()
    }
    return final_dict, capture_date_dict


def plot_data(timestamps, views):
    uuid_str = str(uuid.uuid4())
    fig, ax = plt.subplots()
    ax.plot(timestamps, views, marker=".")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Views")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(uuid_str, format="svg")
    plt.close(fig)
    with open(uuid_str, "r") as svg_file:
        svg_content = svg_file.read()
    os.remove(uuid_str)
    return svg_content


def generate_html_report(data, capture_date_dict, output_html):
    with open(output_html, "w") as f:
        f.write("<html><body>\n")
        f.write("<h1>Image Views Report</h1>\n")

        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(plot_data, url, timestamps, views): url
                for url, (timestamps, views) in data.items()
            }
            for future in tqdm(futures, total=len(data)):
                url = futures[future]
                try:
                    svg_content = future.result()
                    f.write(
                        f"<b>Image Capture Date:</b> {capture_date_dict[url]}<br>\n"
                    )
                    f.write('<div style="display: flex; align-items: center;">\n')
                    f.write(
                        f'<div style="margin-right: 20px;"><img src="{url}" alt="Image" width="300"></div>\n'
                    )
                    f.write("<div>\n")
                    f.write(svg_content)
                    f.write("</div>\n")
                    f.write("</div>\n")
                except Exception as e:
                    print(f"Failed to load or plot image from {url}: {e}")

        f.write("</body></html>\n")


if __name__ == "__main__":
    folder_path = "Data"
    combined_dict, capture_date_dict = combine_dictionaries(folder_path)
    output_html = "index.html"
    generate_html_report(combined_dict, capture_date_dict, output_html)
    print(f"HTML report generated: {output_html}")
