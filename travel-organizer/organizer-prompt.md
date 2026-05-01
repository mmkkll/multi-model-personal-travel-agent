# Travel Organizer — 11-step prompt

This is the prompt the Claude Code session executes on each cron firing.

Replace placeholders before use:
- `${TELEGRAM_CHAT_ID}` — your chat ID
- `${NOTION_TRAVEL_INSPIRATIONS_ID}`, `${NOTION_TRAVEL_PLANNING_ID}`, `${NOTION_TRAVEL_BUSINESS_WORK_ID}`, `${NOTION_TRAVEL_READY_ID}`, `${NOTION_TRAVEL_PAST_TRIPS_ID}` — your Notion page IDs

```
Organize travel documents. Search Gmail for booking confirmations and speaker/conference invitations, classify, match against existing Notion travel pages, create or update pages, and run housekeeping (48h checklist, departure-day auto-move, 5-7d advance notice for work trips, archive past trips).

1. SEARCH GMAIL (last 3h). Two queries in parallel:

   a) BOOKING CONFIRMATIONS:
      is:unread (subject:(confirmation OR conferma OR booking OR reservation OR prenotazione OR itinerary OR e-ticket OR receipt OR boarding OR voucher OR autonoleggio) OR from:(trenitalia OR italotreno OR lufthansa OR swiss OR ita-airways OR vueling OR ryanair OR easyjet OR booking.com OR marriott OR expedia OR hotels.com OR hertz OR europcar OR avis OR thefork OR opentable OR getyourguide OR viator OR airbnb OR centauro OR recordgo OR sixt OR goldcar OR firefly OR octorate OR drivalia OR budget OR alamo OR enterprise OR thrifty OR dollar)) newer_than:3h

   b) INDIRECT SIGNALS (speaker / panel / event invitations):
      is:unread (subject:(panel OR speech OR talk OR keynote OR speaker OR relatori OR relatore OR intervento OR partecipazione OR invito OR invitation OR conference OR forum OR summit OR retreat OR workshop OR webinar OR briefing OR programma OR agenda) OR ("ti aspettiamo" OR "ti invito" OR "save the date")) -from:noreply* -from:no-reply* -from:notification* -from:donotreply* newer_than:3h

2. PER EACH EMAIL FOUND, read full content and extract:

   CATEGORY 1 (Booking confirmation — flight / train / hotel / car / restaurant / experience):
   - Destination / city
   - Check-in / check-out dates, departure / arrival times
   - Booking code / PNR
   - Carrier / company / airline / hotel name, addresses, seats
   - PDF attachments → download

   CATEGORY 2 (Indirect travel signal — panel / speech / event invitation):
   - Event location (city + venue)
   - Date / time
   - Your role (speaker / moderator / panelist / keynote / audience)
   - Organizer (name + email)
   - Co-speakers / moderator if any
   - Brief / questions if received
   - Event title, topic of intervention if specified
   - PDF attachments (program, save-the-date) → download

   CLASSIFICATION work / leisure / ambiguous (for Category 2):
   - WORK if: speaker / moderator / keynote / panelist / committee / advisory / workshop teacher role; OR organizer is company / institution / conference / university
   - LEISURE if: personal invitation to vacation / social event / celebration / ceremony from personal contact
   - AMBIGUOUS if: unclear (e.g., conference where you might be paying audience; weekend retreat mixing networking + leisure)
   - If AMBIGUOUS → message Telegram chat ${TELEGRAM_CHAT_ID} with: subject, sender, 2-line snippet, ask "Business or Leisure? (B/L)" — wait for reply before creating page

3. MATCHING with existing trips. Use Notion fetch on these parents:
   - Inspirations (${NOTION_TRAVEL_INSPIRATIONS_ID})
   - Planning (${NOTION_TRAVEL_PLANNING_ID})
   - business/work (${NOTION_TRAVEL_BUSINESS_WORK_ID})
   - Ready to Travel (${NOTION_TRAVEL_READY_ID})

   Match by destination/city + date window overlap (±3 days).

   Create/update logic:
   - Page exists in Inspirations → move to Planning + add details
   - Page exists in Planning / business-work / Ready → append details
   - No existing page:
     - Category 1 (booking) → CREATE in Planning, title "✈️ Destination — Dates"
     - Category 2 WORK → CREATE in business/work, title "✈️ Destination — Event (dates)"
     - Category 2 LEISURE → CREATE in Planning (later cron will move to Ready on departure day)
     - Category 2 AMBIGUOUS → DO NOT create until user replies B/L

4. PAGE STRUCTURE on Notion. Each travel page must have these sections (add only relevant ones):
   - ## ✈️ Flights (table: Route, Flight, Date, Time, Seat, Booking)
   - ## 🚆 Trains (table: Route, Train, Date, Time, Seat, PNR)
   - ## 🏨 Hotels (per hotel: Name, Address, Check-in/out, Booking code, Price)
   - ## 🚗 Car rentals (Company, Pickup/Return, Dates, Booking code)
   - ## 🍽️ Restaurants (Name, Address, Date/Time, Persons, Booking code)
   - ## 🎫 Experiences (Name, Date/Time, Location, Booking code)
   - ## 📎 Documents (PDF attachments uploaded)

5. NOTIFY TELEGRAM (chat ${TELEGRAM_CHAT_ID}) ONLY if at least one email was processed:
   📂 TRAVEL ORGANIZER
   ✅ Processed N emails
   For each saved booking:
   - Type + destination + dates
   - Notion page link

   If 0 emails processed, DO NOT send anything (skip Telegram).

6. DO NOT mark emails as read. The user manages reading state.

7. PRE-TRIP CHECKLIST (48h before departure). For each page in Planning:
   a. Read all pages in Planning (${NOTION_TRAVEL_PLANNING_ID})
   b. For each, identify departure date (first flight or train chronologically)
   c. If departure is 46-50 hours from now (window to catch in 2h cycle):
      - Verify completeness: outbound flight/train? Hotel? Return flight/train?
      - Check booking codes / PNRs are present
      - Check boarding passes attached
      - Check destination weather (use WebSearch)
      - Send to Telegram:
        ⏰ PRE-TRIP CHECKLIST — [Destination] (departure in 48h)
        ✅ Items present (flight, hotel, train, etc.)
        ❌ MISSING items (what's missing: hotel? return? boarding pass?)
        🌤️ Weather forecast

        Then ask: "Move trip to Ready to Travel?"
        Wait for user confirmation on Telegram before moving.

8. DEPARTURE DAY AUTO-MOVE. For each page in Planning:
   a. If departure date is TODAY:
      - **Determine if work or personal**: search keywords in title or page content (speech, speaker, talk, panel, moderate, keynote, conference, forum, expo, fair, summit, retreat, committee, advisory, event, edition, hospitality, tourism + your role). If YES → work. Else personal.
      - If WORK: move to **business/work** (parent ${NOTION_TRAVEL_BUSINESS_WORK_ID})
      - If PERSONAL: move to **Ready to Travel** (parent ${NOTION_TRAVEL_READY_ID})
      - Notify Telegram:
        🧳 TRIP MOVED TO [BUSINESS/WORK | READY TO TRAVEL]
        ✈️ [Destination] — departure today
        📄 Notion page link
      - DO NOT ask confirmation — automatic on departure day.

9. ADVANCE NOTICE — WORK TRIPS 5-7 DAYS BEFORE. For each page in business/work:
   a. Calculate departure_date from title or ✈️ Flights/🚆 Trains (first leg).
   b. If 5 ≤ (departure_date - today) ≤ 7 days:
      - Verify completeness: flights/trains booked? Hotel? Speech/talk slides ready? Brief received? Bio updated?
      - Extract TODO list from 📋 TODO section of the page
      - Telegram:
        🎤 PREP REMINDER — [Destination] in X days
        Events: [list of talks/panels with times]
        ❌ Open TODOs: [bullet list from TODO section]
        ✅ Completed: [items already done]
        Start preparing slides/content.
   c. If departure_date ≤ 2 days: also send standard pre-trip checklist (logistics). Run AFTER step 7.

   To avoid spam, only send advance notice once per day per trip — track sent notices in a small state file (e.g., `~/.travel-agent/advance-notice-sent.json`).

10. AUTO-ARCHIVE POST-TRIP. For each page in Ready to Travel **AND** business/work:
    a. Extract trip end date from title or ✈️ Flights section (last return flight).
    b. If end_date < today:
       - Move page to 📦 Past trips (parent ${NOTION_TRAVEL_PAST_TRIPS_ID})
       - DO NOT notify Telegram (silent housekeeping)
    c. Run AFTER steps 8 and 9.

11. (Optional) TASK MANAGER SYNC. If you use a task manager (Sunsama, Todoist, Things, etc.) you can add a step here that creates/updates a task per business/work trip with TODOs. This is integration-specific and not included by default — see your task manager's API docs.
```

## Adapting for your task manager

If you want step 11 (task manager sync), the typical pattern:

```
For each page in business/work within 45 days from today:
   a. Search task manager for existing task matching this trip (e.g., by Notion URL in notes)
   b. If not found → create task with:
      - title: "✈️ <trip title>"
      - notes: Notion URL + summary + TODOs from page
      - due date: trip end date
      - schedule date: trip start date
   c. If exists → update if changed
```

Common APIs:
- Todoist: https://developer.todoist.com/rest/v2/
- Things: AppleScript / URL scheme
- TickTick: https://developer.ticktick.com/
- Linear: https://developers.linear.app/
- Notion (as task DB): https://developers.notion.com/
