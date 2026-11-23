# openrouteservice API

## Purpose

openrouteservice is used by SkyWatch to determine reachable areas, find candidate observation locations, and calculate routes to selected locations.

## Official Documentation

https://openrouteservice.org/dev/#/api-docs

## Used Endpoints

### `POST /v2/isochrones/driving-car`

Returns the area that can be reached from a selected location within a specified travel time or distance.

Used input data:
- user coordinates
- travel profile
- maximum travel time or distance

Used output data:
- reachable area as GeoJSON polygon
- center coordinates
- travel range

Test result: successful. A 30-minute reachable driving area was successfully generated from the selected starting location.

### `POST /openpoiservice/v0/pois`

Returns points of interest within a selected area.

Used input data:
- coordinates or search area
- search radius
- POI categories
- result limit

Used output data:
- candidate location coordinates
- distance from the search point
- POI category
- location name when available

Test result: successful. The API returned multiple candidate locations, including parks and natural peaks such as Drenikov vrh.

### `POST /v2/directions/driving-car/geojson`

Calculates a route between two locations.

Used input data:
- starting coordinates
- destination coordinates
- travel profile

Used output data:
- route distance
- route duration
- navigation steps
- route geometry

Test result: successful. The tested route returned a distance of 3433 m and a duration of 498.4 seconds. 

## Data Format

GeoJSON / JSON

## Authentication

An API key is required.

## Usage in SkyWatch

SkyWatch uses openrouteservice to determine which areas are reachable from the user's location, identify candidate observation locations, and calculate a route to the selected destination.

The candidate locations can then be evaluated together with weather data from Open-Meteo in order to recommend a more suitable observation location.
