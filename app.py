from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os

app = Flask(__name__)
# ✅ Allow all origins for cross-origin requests (fixes 403 error)
CORS(app, resources={r"/*": {"origins": "*"}})

# HSV color ranges
color_ranges = {
    "black": [(0, 0, 0), (180, 255, 70)],
    "white": [(0, 0, 200), (180, 60, 255)],
    "gray": [(0, 0, 71), (180, 60, 199)],
    "red": [(170, 180, 50), (179, 255, 255)],
    "orange": [(17, 190, 252), (17, 190, 252)],
    "yellow": [(26, 100, 100), (34, 255, 255)],
    "green": [(35, 50, 50), (85, 255, 255)],
    "cyan": [(86, 100, 100), (95, 255, 255)],
    "blue": [(96, 100, 100), (130, 255, 255)],
    "purple": [(131, 50, 50), (160, 255, 255)],
    "pink": [(161, 50, 50), (169, 255, 255)],
    "brown": [(10, 30, 50), (30, 180, 255)]
}

def decode_base64_image(base64_data):
    header, encoded = base64_data.split(",", 1)
    img_data = base64.b64decode(encoded)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def calculate_color_percentage_with_swatches(roi):
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    total_pixels = hsv.shape[0] * hsv.shape[1]
    raw_counts = {}
    swatches = {}

    for color, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        count = cv2.countNonZero(mask)
        raw_counts[color] = count

        if count > 0:
            masked_pixels = roi[mask > 0]
            avg_bgr = np.mean(masked_pixels, axis=0)
            b, g, r = map(int, avg_bgr)
            swatches[color] = f"rgb({r},{g},{b})"

    filtered = {color: count for color, count in raw_counts.items() if count > 0}
    total_color_pixels = sum(filtered.values())

    if total_color_pixels == 0:
        return {}

    percentages = {
        color: round((count / total_color_pixels) * 100, 2)
        for color, count in filtered.items()
    }

    total_percent = sum(percentages.values())
    if percentages and total_percent != 100:
        diff = round(100 - total_percent, 2)
        max_color = max(percentages, key=percentages.get)
        percentages[max_color] = round(percentages[max_color] + diff, 2)

    result = {
        color: {
            "percent": percentages[color],
            "swatch": swatches.get(color, "rgb(0,0,0)")
        }
        for color in percentages
    }

    return result

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        image = decode_base64_image(data['image'])
        results = calculate_color_percentage_with_swatches(image)
        return jsonify({"colors": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    app.run(host='0.0.0.0', port=port)
