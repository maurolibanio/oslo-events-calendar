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

VISIT_OSLO_BASE = "https://www.visitoslo.com"

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
            VISIT_OSLO_BASE
            + url
        )

    description_parts = []

    if description:
        description_parts.append(
            description
        )

    if url:
        description_parts.append("")
        description_parts.append(
            f"Visit Oslo: {url}"
        )

    full_description = "\n".join(
        description_parts
    )

    openings = (
        item.get("openingHours")
        or []
    )

    if openings:

        for opening in openings:

            try:

                opening_times = (
                    opening.get(
                        "openingTimes"
                    )
                    or []
                )

                closing_times = (
                    opening.get(
                        "closingTimes"
                    )
                    or []
                )

                start_dt = None
                end_dt = None

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

                if closing_times:

                    end_dt = (
                        datetime.fromisoformat(
                            closing_times[0]
                        )
                    )

                else:

                    end_dt = (
                        start_dt
                        + timedelta(hours=2)
                    )

                event = Event()

                event.add(
                    "summary",
                    title
                )

                if full_description:
                    event.add(
                        "description",
                        full_description
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

                    uid = (
                        f"{event_id}-"
                        f"{start_dt.strftime('%Y%m%d%H%M%S')}"
                        "@oslo-events-calendar"
                    )

                    event.add(
                        "uid",
                        uid
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

            event = Event()

            event.add(
                "summary",
                title
            )

            if full_description:
                event.add(
                    "description",
                    full_description
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

                uid = (
                    f"{event_id}-"
                    f"{start_dt.strftime('%Y%m%d%H%M%S')}"
                    "@oslo-events-calendar"
                )

                event.add(
                    "uid",
                    uid
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

    cal.add_component(
        event
    )

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
