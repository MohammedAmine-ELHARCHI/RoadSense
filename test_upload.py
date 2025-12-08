import requests

url = "http://localhost:8001/api/v1/detection/detect"

# Create a simple test image (1x1 red pixel)
import io
from PIL import Image
import numpy as np

img = Image.fromarray(np.uint8([[[255, 0, 0]]]))
buf = io.BytesIO()
img.save(buf, format='JPEG')
buf.seek(0)

files = {'image': ('test.jpg', buf, 'image/jpeg')}

try:
    response = requests.post(url, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
