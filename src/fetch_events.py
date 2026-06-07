import json
import requests
from datetime import date, timedelta

today = date.today()
future = today + timedelta(days=365)

url = (
    "https://www.visitoslo.com/api/eventlist/events"
    "?pageId=837"
    "&language=en"
    "&offset=0"
    "&CategoryIds=505552,506042,507212,507232,"
    "505772,506922,506802,519862,506032,"
    "513572,506232,505792,500602,"
    "508172,508182,502032,507222,509172"
    f"&FromDate={today.isoformat()}"
    f"&ToDate={future.isoformat()}"
)

response = requests.get(url)
response.raise_for_status()

data = response.json()

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"Downloaded {len(data['events'])} events "
    f"from {today} to {future}"
)
