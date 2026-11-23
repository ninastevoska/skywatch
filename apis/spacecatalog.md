# SpaceCatalog API

## Purpose

SpaceCatalog provides astronomical event data and object visibility information used by SkyWatch for event discovery and observation planning.

## Official Documentation

https://spacecatalog.org/api

## Used Endpoints

### `GET /api/v1/events`

Returns astronomical events within a selected time range.

Used data:
- event type
- date and time
- title and description
- related celestial objects
- sky position
- event-specific parameters

Test result: successful. The API returned multiple event types, including lunar phases, conjunctions, oppositions, elongations, and meteor showers. 

### `GET /api/v1/visible`

Returns celestial objects visible above a selected altitude for a given location and time.

Used data:
- object name and type
- altitude
- azimuth
- direction
- apparent magnitude
- Sun condition

Test result: successful. The response correctly returned visible objects for the selected observer location and time. 

### `GET /api/v1/ephemeris`

Returns detailed observation data for a selected celestial object.

Used data:
- rise, transit and set times
- observable time window
- best observation time
- altitude and azimuth
- Moon phase and separation
- object track during the night

Test result: successful. The response provided the observation window, best observation time and detailed night track for Saturn. 

## Data Format

JSON

## Authentication

No API key is required.

## Usage in SkyWatch

SkyWatch uses SpaceCatalog to identify upcoming astronomical events, determine which celestial objects are visible from a selected location, and calculate suitable observation times.