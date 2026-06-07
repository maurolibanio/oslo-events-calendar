from icalendar import Calendar, Event
from datetime import datetime
import json
import os

calendar = Calendar()
calendar.add("prodid", "-//Oslo Events Calendar//")
calendar.add("version", "2.0")

with open("events.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data["events"]:

    event = Event()

    title = item.get("title", "Untitled Event")

    start = item.get("fromDate")

    if not start:
        continue

    event.add("summary", title)
    event.add("dtstart", datetime.fromisoformat(start))
    event.add("description", item.get("description", {}).get("shortPlainText", ""))
    event.add("location", item.get("place", ""))

    url = item.get("url")

    if url:
        event.add(
            "url",
            f"https://www.visitoslo.com{url}"
        )

    calendar.add_component(event)

os.makedirs("docs", exist_ok=True)

with open("docs/oslo-all.ics", "wb") as f:
    f.write(calendar.to_ical())

print("ICS generated")
