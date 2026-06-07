# Oslo Events Calendar

A free public calendar feed that automatically synchronizes events from Visit Oslo and makes them available through a standard iCalendar (ICS) subscription. Not all filters enabled, working on it - but most of events already being populated. :)

## Disclaimer

This project is a personal, non-commercial initiative created and maintained independently by its author.

It is not affiliated with, endorsed by, sponsored by, or maintained by Visit Oslo.

All event information remains the property of its respective owners and is sourced from publicly available data provided by Visit Oslo.

The purpose of this project is to make publicly available event information easier to consume through standard calendar applications by providing an automatically generated iCalendar (ICS) feed.

This project:

* Is not affiliated with Visit Oslo.
* Is not endorsed, sponsored, approved, or maintained by Visit Oslo.
* Does not represent Visit Oslo in any capacity.
* Does not charge users for access to event information.
* Does not claim ownership of any event data, descriptions, images, trademarks, or other content originating from Visit Oslo or event organizers.

Event information is sourced from publicly accessible data provided by Visit Oslo and remains the property of its respective owners.

If you represent Visit Oslo or an event organizer and have concerns regarding this project, please open an issue in this repository and the matter will be reviewed promptly.

All information is provided "as is" without any warranty regarding accuracy, completeness, availability, or timeliness.

## Live Calendar Feed

**Subscribe URL**

```text
https://maurolibanio.github.io/oslo-events-calendar/oslo-all.ics
```

## How to Subscribe

### Google Calendar

1. Open Google Calendar.
2. Click the **+** next to **Other calendars**.
3. Select **From URL**.
4. Paste the calendar URL.
5. Click **Add calendar**.

### Apple Calendar

1. Open Calendar.
2. Select **Add Subscription Calendar**.
3. Paste the calendar URL.
4. Save.

### Outlook

1. Open Outlook Calendar.
2. Click **Add Calendar**.
3. Select **Subscribe from Web**.
4. Paste the calendar URL.
5. Save.

---

## Synchronization

### Event Source

Events are retrieved from the public Visit Oslo event API.

Source:

https://www.visitoslo.com/

### Feed Updates

This repository automatically:

1. Downloads the latest events from Visit Oslo.
2. Generates a fresh ICS calendar.
3. Publishes the updated feed through GitHub Pages.

### Update Frequency

The feed is automatically regenerated every hour via GitHub Actions.

### Important Note About Calendar Apps

Calendar applications control their own refresh intervals.

Typical synchronization delays:

| Calendar Application | Typical Refresh Interval         |
| -------------------- | -------------------------------- |
| Google Calendar      | Several hours to 24 hours        |
| Apple Calendar       | Usually within a few hours       |
| Outlook              | Depends on platform and settings |

As a result, newly added events may not appear immediately even though the feed itself has already been updated.

---

## Project Architecture

```text
Visit Oslo API
       ↓
GitHub Actions
       ↓
Python Processing
       ↓
ICS Generation
       ↓
GitHub Pages
       ↓
Google Calendar / Apple Calendar / Outlook
```

---

## Contributing

Suggestions, bug reports, and improvements are welcome.

Please open an Issue or Pull Request.

---

## License

MIT License.

