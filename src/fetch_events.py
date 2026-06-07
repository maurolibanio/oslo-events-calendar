import json
import requests

url = (
    "https://www.visitoslo.com/api/eventlist/events"
    "?pageId=837"
    "&language=en"
    "&offset=0"
    "&CategoryIds=505552,506042,507212,507232,"
    "505772,506922,506802,519862,506032,"
    "513572,506232,505792,500602,"
    "508172,508182,502032,507222,509172"
)

response = requests.get(url)

response.raise_for_status()

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(
        response.json(),
        f,
        ensure_ascii=False,
        indent=2
    )

print("Events downloaded")
