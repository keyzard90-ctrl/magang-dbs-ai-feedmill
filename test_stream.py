import requests
import json

url = "http://192.168.192.96:5001/api/stream_data"
try:
    with requests.get(url, stream=True, timeout=5) as r:
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    data_str = decoded_line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        print("RECEIVED DATA:")
                        print(f"Total count: {data.get('total_count')}")
                        print(f"Boxes length: {len(data.get('boxes', []))}")
                        print(f"Boxes: {data.get('boxes', [])}")
                        break
                    except json.JSONDecodeError:
                        print("Failed to decode JSON")
except Exception as e:
    print(f"Error: {e}")
