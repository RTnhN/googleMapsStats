import os
import csv
from collections import defaultdict
from datetime import datetime
import matplotlib

matplotlib.use("Agg")  # Use the 'Agg' backend for background plot generation
import matplotlib.pyplot as plt

from tqdm import tqdm


def dict_merge(dict1, dict2):
    combined = {}

    # Combine values, prioritizing non-"Unknown" values
    for key in set(dict1) | set(dict2):  # Union of keys from both dictionaries
        value1 = dict1.get(key, "Unknown")
        value2 = dict2.get(key, "Unknown")

        if value1 != "Unknown":
            combined[key] = value1
        elif value2 != "Unknown":
            combined[key] = value2
        else:
            combined[key] = "Unknown"

    return combined


# Function to process each CSV file
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


# Function to extract the timestamp from the filename
def extract_timestamp(file_name):
    # Remove extension and split on '+' character
    file_name_no_ext = os.path.splitext(file_name)[0]
    parts = file_name_no_ext.split("+")
    if len(parts) > 1:
        timestamp_str = parts[-1]  # Get the right-hand side (timestamp)

        # Remove invalid characters and parse the timestamp
        timestamp_str = (
            timestamp_str.replace("_", ":").replace("T", " ").replace("Z", "")
        )
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

    return None


# Main function to combine the dictionaries
def combine_dictionaries(folder_path):
    combined_dict = defaultdict(list)  # Store URLs with lists of views by timestamp
    capture_date_dict = {}

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            # Extract the timestamp
            timestamp = extract_timestamp(file_name)
            if timestamp:
                file_path = os.path.join(folder_path, file_name)
                views_data, capture_data = process_csv(file_path)
                capture_date_dict = dict_merge(capture_date_dict, capture_data)

                # Add each entry to the combined dictionary
                for url, views in views_data.items():
                    combined_dict[url].append((timestamp, views))

    # Sort the views list for each URL by timestamp
    for url in combined_dict:
        combined_dict[url].sort(key=lambda x: x[0])  # Sort by the timestamp

    # Convert (timestamp, views) tuples to just views, keeping them in date-ascending order
    final_dict = {
        url: (list(zip(*views_list))[0], [views for _, views in views_list])
        for url, views_list in combined_dict.items()
    }

    return final_dict, capture_date_dict


# Function to generate HTML with embedded SVG plots and images, side by side
def generate_html_report(data, capture_date_dict, output_html):
    svg_filename = "tmp.svg"
    with open(output_html, "w") as f:
        f.write("<html><body>\n")
        f.write("<h1>Image Views Report</h1>\n")

        for idx, (url, (timestamps, views)) in tqdm(
            enumerate(data.items()), total=len(data)
        ):
            try:
                # Create a plot for views over time (this will now be done in the background)
                fig, ax = plt.subplots()
                ax.plot(timestamps, views, marker=".")
                ax.set_xlabel("Time (UTC)")
                ax.set_ylabel("Views")
                fig.autofmt_xdate()  # Automatically rotates and formats the dates

                # Save the plot as an SVG file
                fig.tight_layout()  # Adjust the layout to avoid overlap

                fig.savefig(svg_filename, format="svg")

                # Close the figure to free up memory
                plt.close(fig)

                # Write the image and the plot to the HTML file, side by side
                f.write(f"<b>Image Capture Date:</b> {capture_date_dict[url]}<br>\n")
                f.write('<div style="display: flex; align-items: center;">\n')

                # Embed the image in one div
                f.write(
                    f'<div style="margin-right: 20px;"><img src="{url}" alt="Image" width="300"></div>\n'
                )

                # Embed the SVG plot in another div
                f.write("<div>\n")
                with open(svg_filename, "r") as svg_file:
                    svg_content = svg_file.read()
                    f.write(svg_content)
                f.write("</div>\n")

                # Close the div
                f.write("</div>\n")

            except Exception as e:
                print(f"Failed to load or plot image from {url}: {e}")

        f.write("</body></html>\n")

    os.remove(svg_filename)


# Example usage:
folder_path = "Data"
combined_dict, capture_date_dict = combine_dictionaries(folder_path)

# Generate the HTML report
output_html = "index.html"
generate_html_report(combined_dict, capture_date_dict, output_html)

print(f"HTML report generated: {output_html}")
