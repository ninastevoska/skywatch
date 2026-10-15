# SkyWatch – Data Model

A Python console application for processing astronomical events, observation locations, and weather data. It loads related XML datasets, connects records using unique identifiers, allows interactive filtering, and exports results to JSON and XML.

## Data Sources

- **Astronomical events:** SpaceCatalog.org
- **Observation locations:** OpenStreetMap (via openpoiservice)
- **Weather data:** Open-Meteo (historical weather and forecasts)

The `data/` directory contains three XML datasets:

- `events.xml` – 17 astronomical events
- `locations.xml` – 26 observation locations
- `observations.xml` – 17 observations linked to events and locations, with optional weather data

## Requirements

- Python 3.10 or newer
- No additional packages required

## How to Run

1. Download or clone the project.
2. Open a terminal in the `data-model` directory (the folder containing `main.py`).
3. Run:

   ```bash
   python main.py
   ```

   On systems where Python is invoked as `python3`, use `python3 main.py`.

## Features

The console menu supports:

- Browsing all astronomical events and observations
- Filtering by event type and starting date
- Filtering observations by maximum cloud cover
- Combining multiple filters

After filtering, the application displays the results and automatically saves them in the `data-model/output` directory as:

- `filtrirano.json`
- `filtrirano.xml`

Both files are overwritten when a new filter is applied.

## Project Structure

```text
data-model/
├── data/
│   ├── events.xml
│   ├── locations.xml
│   └── observations.xml
├── src/
│   ├── models.py
│   ├── xml_reader.py
│   ├── data_service.py
│   ├── filters.py
│   └── exporters.py
├── output/
│   ├── filtrirano.json
│   └── filtrirano.xml
├── main.py
└── README.md
```

The `src/` modules define data models, read XML files, connect records, apply filters, and export results.