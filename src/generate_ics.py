import json

from datetime import (
    datetime,
    timedelta,
    timezone
)

from icalendar import (
    Calendar,
    Event
)

cal = Calendar()

cal.add(
    "prodid",
    "-//Oslo Events Calendar//"
)

cal.add(
    "version",
    "2.0"
)

cal.add(
    "x-wr-calname",
    "Oslo Events"
)

cal.add(
    "x-wr-timezone",
    "Europe/Oslo"
)

with open(
    "events.json",
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)

events = data.get("events", [])

calendar_events = []

generated = 0

for item in events:

    title = item.get("title") or "Untitled Event"

    description_data = (
        item.get("description")
        or {}
    )

    description = (
        description_data.get(
            "shortPlainText"
        )
        or description_data.get(
            "longPlainText"
        )
        or ""
    )

    place = item.get("place") or ""
    intro = item.get("intro") or ""

    location = " - ".join(
        x for x in [intro, place] if x
    )

    url = item.get("url")

    if url and url.startswith("/"):
        url = (
            "https://www.visitoslo.com"
            + url
        )

    openings = (
        item.get("openingHours")
        or []
    )

    if openings:

        for idx, opening in enumerate(openings):

            try:

                start_dt = None

                opening_times = (
                    opening.get(
                        "openingTimes"
                    )
                    or []
                )

                if opening_times:

                    start_dt = (
                        datetime.fromisoformat(
                            opening_times[0]
                        )
                    )

                elif opening.get("startDay"):

                    start_dt = (
                        datetime.fromisoformat(
                            opening["startDay"]
                        )
                    )

                if not start_dt:
                    continue

                event = Event()

                event.add(
                    "summary",
                    title
                )

                if description:
                    event.add(
                        "description",
                        description
                    )

                if location:
                    event.add(
                        "location",
                        location
                    )

                event.add(
                    "dtstart",
                    start_dt
                )

                event.add(
                    "dtend",
                    start_dt
                    + timedelta(hours=2)
                )

                event.add(
                    "dtstamp",
                    datetime.now(
                        timezone.utc
                    )
                )

                event_id = item.get("id")

                if event_id:

                    event.add(
                        "uid",
                        f"{event_id}-{idx}"
                        "@oslo-events-calendar"
                    )

                if url:
                    event.add(
                        "url",
                        url
                    )

                calendar_events.append(
                    (
                        start_dt,
                        event
                    )
                )

                generated += 1

            except Exception as e:

                print(
                    f"OpeningHours error "
                    f"{item.get('id')}: "
                    f"{e}"
                )

    else:

        try:

            event = Event()

            event.add(
                "summary",
                title
            )

            if description:
                event.add(
                    "description",
                    description
                )

            if location:
                event.add(
                    "location",
                    location
                )

            start = (
                item.get("fromTime")
                or item.get("fromDate")
            )

            end = (
                item.get("toTime")
                or item.get("toDate")
            )

            if not start:
                continue

            start_dt = (
                datetime.fromisoformat(
                    start
                )
            )

            if end:

                end_dt = (
                    datetime.fromisoformat(
                        end
                    )
                )

            else:

                end_dt = (
                    start_dt
                    + timedelta(hours=2)
                )

            event.add(
                "dtstart",
                start_dt
            )

            event.add(
                "dtend",
                end_dt
            )

            event.add(
                "dtstamp",
                datetime.now(
                    timezone.utc
                )
            )

            event_id = item.get("id")

            if event_id:

                event.add(
                    "uid",
                    f"{event_id}"
                    "@oslo-events-calendar"
                )

            if url:
                event.add(
                    "url",
                    url
                )

            calendar_events.append(
                (
                    start_dt,
                    event
                )
            )

            generated += 1

        except Exception as e:

            print(
                f"Event error "
                f"{item.get('id')}: "
                f"{e}"
            )

calendar_events.sort(
    key=lambda x: x[0]
)

for _, event in calendar_events:
    cal.add_component(event)

with open(
    "docs/oslo-all.ics",
    "wb"
) as f:

    f.write(
        cal.to_ical()
    )

print(
    f"Generated "
    f"{generated} "
    f"calendar entries"
)
