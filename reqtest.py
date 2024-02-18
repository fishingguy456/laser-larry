import requests
URL = {"xy": "http://192.168.2.144/xy"}
data = {"x": 1, "y": 0.5}
r = requests.post(URL["xy"], json=data)
print(r)
