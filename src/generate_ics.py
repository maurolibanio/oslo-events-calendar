from icalendar import Calendar, Event
from datetime import datetime
import json

cal = Calendar()
cal.add("prodid", "-//Oslo Events Calendar//")
cal.add("version", "2.0")

with open("events.json", "r", encoding="utf-8") as f:
    data = json.load(f)

events = data.get("events", [])

generated = 0

for item in events:

    title = item.get("title") or "Untitled Event"

    description_data = item.get("description") or {}

    description = (
        description_data.get("shortPlainText")
        or description_data.get("longPlainText")
        or ""
    )

    place = item.get("place") or ""
    intro = item.get("intro") or ""

    location = " - ".join(
        x for x in [intro, place] if x
    )

    url = item.get("url")
    if url and url.startswith("/"):
        url = "https://www.visitoslo.com" + url

    openings = item.get("openingHours") or []

    if openings:

        for idx, opening in enumerate(openings):

            try:

                start_day = opening.get("startDay")

                if not start_day:
                    continue

                event = Event()

                event.add("summary", title)

                if description:
                    event.add("description", description)

                if location:
                    event.add("location", location)

                start_dt = datetime.fromisoformat(start_day)

                event.add("dtstart", start_dt)
                event.add("dtend", start_dt)

                event_id = item.get("id")

                if event_id:
                    event.add(
                        "uid",
                        f"{event_id}-{idx}@oslo-events-calendar"
                    )

                if url:
                    event.add("url", url)

                cal.add_component(event)

                generated += 1

            except Exception as e:
                print(
                    f"OpeningHours error "
                    f"{item.get('id')}: {e}"
                )

    else:

        try:

            event = Event()

            event.add("summary", title)

            if description:
                event.add("description", description)

            if location:
                event.add("location", location)

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

            event_id = item.get("id")

            if event_id:
                event.add(
                    "uid",
                    f"{event_id}@oslo-events-calendar"
                )

            if url:
                event.add("url", url)

            cal.add_component(event)

            generated += 1

        except Exception as e:
            print(
                f"Event error "
                f"{item.get('id')}: {e}"
            )

with open("docs/oslo-all.ics", "wb") as f:
    f.write(cal.to_ical())

print(f"Generated {generated} calendar entries")
