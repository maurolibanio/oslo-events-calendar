from icalendar import Calendar, Event
from datetime import datetime
import json

cal = Calendar()
cal.add("prodid", "-//Oslo Events Calendar//")
cal.add("version", "2.0")

with open("events.json", "r", encoding="utf-8") as f:
    data = json.load(f)

events = data.get("events", [])

for item in events:
    try:
        event = Event()

        title = item.get("title") or "Untitled Event"
        event.add("summary", title)

        description = item.get("description") or {}

        event.add(
            "description",
            description.get("shortPlainText")
            or description.get("longPlainText")
            or ""
        )

        start = item.get("fromTime") or item.get("fromDate")
        end = item.get("toTime") or item.get("toDate")

        if start:
            event.add(
                "dtstart",
                datetime.fromisoformat(start)
            )

        if end:
            event.add(
                "dtend",
                datetime.fromisoformat(end)
            )

        place = item.get("place") or ""
        intro = item.get("intro") or ""

        location = " - ".join(
            x for x in [intro, place] if x
        )

        if location:
            event.add("location", location)

        event_id = item.get("id")
        if event_id:
            event.add(
                "uid",
                f"{event_id}@oslo-events-calendar"
            )

        url = item.get("url")
        if url:
            if url.startswith("/"):
                url = "https://www.visitoslo.com" + url

            event.add("url", url)

        cal.add_component(event)

    except Exception as e:
        print(
            f"Skipping event "
            f"{item.get('id')} - "
            f"{item.get('title')} "
            f"because: {e}"
        )

with open(
    "docs/oslo-all.ics",
    "wb"
) as f:
    f.write(cal.to_ical())

print(
    f"Generated calendar with "
    f"{len(events)} events"
)
