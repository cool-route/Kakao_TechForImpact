import requests
import xmltodict
import json

API_KEY = "네 인증키"

url = (
    "https://apis.data.go.kr/1741000/"
    "HealthSheltersForEachRegion/"
    "getHealthSheltersForEachRegion"
)

params = {
    "serviceKey": API_KEY,
    "pageNo": 1,
    "numOfRows": 100
}

response = requests.get(url, params=params)

print(response.status_code)

print(response.text[:1000])