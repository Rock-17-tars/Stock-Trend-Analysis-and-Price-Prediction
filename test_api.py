import requests
import pandas as pd

API_KEY = "84626b8618a3fa8d2191d6247c679b76"
url = f"http://api.marketstack.com/v1/eod?access_key={API_KEY}&symbols=AAPL"

res = requests.get(url)
print(res.json())
