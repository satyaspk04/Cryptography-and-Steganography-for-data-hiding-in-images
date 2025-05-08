import os
import requests
from PIL import Image
import numpy as np
import io
import time
import cv2
from collections import Counter

# VirusTotal API Key (replace with your own key)
VIRUSTOTAL_API_KEY = 'fe31a30a3a48eacc0171d0e422ac71aa7f724bb255b7983db21591ab409a7728'
VIRUSTOTAL_URL = 'https://www.virustotal.com/api/v3/files'


def analyze_image(image_file):
    try:
        # Read the image data
        image_data = image_file.read()
        image = Image.open(io.BytesIO(image_data))

        # Get image properties
        width, height = image.size
        resolution = f"{width} x {height}"
        color_complexity = np.std(np.array(image))
        noise_level = np.sum(np.abs(np.array(image) - np.mean(np.array(image))))
        estimated_capacity = f"{(width * height) // 8} bytes"
        success_rate = "100%"

        #  Detect Blur Level
        blur_level = detect_blur(io.BytesIO(image_data))

        #  Extract Dominant Color
        dominant_color = extract_dominant_color(image)

        #  Generate Image Quality Rating (1-10)
        quality_rating = calculate_quality_rating(blur_level, noise_level, color_complexity)

        #  Scan for Virus (Optional)
        filename = image_file.filename or "uploaded_image.png"
        virus_scan_result = scan_file_for_viruses(image_data, filename)

        #  AI Suggestions Result
        ai_suggestions = {
            "Resolution": resolution,
            "Color Complexity": round(color_complexity, 2),
            "Noise Level": round(noise_level, 2),
            "Estimated Capacity": estimated_capacity,
            "Success Rate": success_rate,
            "Blur Level": round(blur_level, 2),
            "Dominant Color": dominant_color,
            "Quality Rating": quality_rating
        }

        #  Combined Result
        result = {
            "ai_suggestions": ai_suggestions,
            "virus_scan": virus_scan_result
        }

        return result

    except Exception as e:
        return {"error": f"Error analyzing image: {str(e)}"}


#  Detect Blur Level (Laplacian variance)
def detect_blur(image_data):
    try:
        img = cv2.imdecode(np.frombuffer(image_data.read(), np.uint8), cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var
    except Exception as e:
        return f"Error detecting blur: {str(e)}"


#  Extract Dominant Color
def extract_dominant_color(image):
    try:
        pixels = np.array(image).reshape(-1, 3)
        most_common = Counter(map(tuple, pixels)).most_common(1)[0][0]
        return f"RGB({most_common[0]}, {most_common[1]}, {most_common[2]})"
    except Exception as e:
        return f"Error detecting dominant color: {str(e)}"


#  Generate Image Quality Rating (Scale 1-10)
def calculate_quality_rating(blur_level, noise_level, color_complexity):
    try:
        # Define ranges for normalization
        blur_score = min(max(blur_level / 1000, 0), 1)  # Normalize between 0 and 1
        noise_score = min(max(1 - (noise_level / 100000), 0), 1)  # Lower noise = higher score
        color_score = min(max(color_complexity / 128, 0), 1)  # More color variety = higher score

        # Weighted average for rating
        quality = (0.4 * blur_score) + (0.3 * noise_score) + (0.3 * color_score)
        rating = int(quality * 10)  # Scale to 1-10

        return rating

    except Exception as e:
        return f"Error calculating quality rating: {str(e)}"


#  Scan File for Viruses using VirusTotal
def scan_file_for_viruses(file_data, filename):
    if not VIRUSTOTAL_API_KEY:
        return {"error": "VirusTotal API key not configured."}

    try:
        files = {'file': (filename, file_data)}
        headers = {'x-apikey': VIRUSTOTAL_API_KEY}

        response = requests.post(VIRUSTOTAL_URL, files=files, headers=headers)
        
        if response.status_code == 200:
            scan_data = response.json()
            analysis_id = scan_data['data']['id']

            result_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            time.sleep(5)

            analysis_response = requests.get(result_url, headers=headers)
            if analysis_response.status_code == 200:
                analysis_data = analysis_response.json()
                stats = analysis_data['data']['attributes']['stats']

                harmless = stats.get('harmless', 0)
                malicious = stats.get('malicious', 0)

                if malicious > 0:
                    return {"status": "Malicious", "harmless_count": harmless, "malicious_count": malicious}
                else:
                    return {"status": "Clean", "harmless_count": harmless, "malicious_count": malicious}
        else:
            return {"error": f"Failed to upload file: {response.text}"}

    except Exception as e:
        return {"error": f"Error scanning file: {str(e)}"}


if __name__ == "__main__":
    test_image = 'test.jpg'
    with open(test_image, 'rb') as img_file:
        result = analyze_image(img_file)
        print(result)
