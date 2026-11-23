# Open-Meteo API

## Purpose

Open-Meteo provides weather forecast data used by SkyWatch to evaluate observing conditions for selected locations and times.

## Official Documentation

https://open-meteo.com/en/docs

## Used Endpoint

### `GET /v1/forecast`

Returns hourly weather forecast data for a selected location.

Used input parameters:
- latitude
- longitude
- hourly weather variables
- forecast period
- timezone

Used output data:
- cloud cover
- precipitation
- visibility
- wind speed
- hourly timestamps

## Data Format

JSON

## Authentication

No API key is required for the planned usage.

## Test Summary

The endpoint was successfully tested for multiple locations. The returned data included hourly weather conditions and correct units for all required variables.

The tests also confirmed that SkyWatch can compare weather conditions between different candidate observation locations.

## Usage in SkyWatch

SkyWatch uses Open-Meteo to evaluate weather conditions at the user's location and at alternative observation locations. These data are combined with astronomical information to determine whether observing conditions are suitable.
