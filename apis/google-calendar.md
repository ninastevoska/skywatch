# Google Calendar API

## Purpose

Google Calendar API is used by SkyWatch to allow users to add selected astronomical events to their personal calendar and receive reminders.

## Official Documentation

https://developers.google.com/calendar/api

## Used Endpoint

### `POST /calendar/v3/calendars/primary/events`

Creates a new event in the authenticated user's primary Google Calendar.

Used input data:
- event title
- description
- location
- start date and time
- end date and time
- timezone
- reminder settings

Used output data:
- event ID
- confirmation status
- calendar event link
- created and updated timestamps
- event details
- reminder configuration

## Data Format

JSON

## Authentication

OAuth 2.0 is required.

SkyWatch uses the `calendar.events` scope:

```text
https://www.googleapis.com/auth/calendar.events

```

## Test Summary

The endpoint was successfully tested by creating a Saturn observation event.

The created event included:
- title: `Saturn Observation`
- location: `Drenikov vrh, Ljubljana`
- observation time
- 30-minute popup reminder

The API returned the event with status `confirmed`.

## Usage in SkyWatch

SkyWatch allows users to add selected astronomical events directly to their Google Calendar.

The calendar event can include the observation time, recommended location, event description, and a reminder before the observation begins.