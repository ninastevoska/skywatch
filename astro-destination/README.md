# AstroDestination Explorer

AstroDestination Explorer is a standalone application developed as part of the **SkyWatch** project. It provides tourism statistics for Slovenian municipalities to support the planning of astronomy-related trips.

The application retrieves open tourism data in PC-Axis format, processes the data, and presents the results through dynamic charts and statistical summaries.

The module is designed for future integration into SkyWatch as an **"About Destination"** section.

## Planned Features

- **Monthly overnight stays:** Display the number of tourist overnight stays by month for a selected municipality and year.
- **Municipality comparison:** Compare tourism statistics between two Slovenian municipalities.
- **Most and least visited months:** Identify the months with the highest and lowest numbers of tourist overnight stays.
- **Tourism trends:** Visualize changes in tourism activity across the available years.

## Data Source

The application uses publicly available tourism statistics published by the **Statistical Office of the Republic of Slovenia (SURS)** through the Slovenian Open Data Portal (OPSI).

**Dataset:** Tourist arrivals and overnight stays by country of origin and municipality, Slovenia, monthly.

- **Dataset page:** https://podatki.gov.si/dataset/surs2164466s
- **Dataset resource:** https://podatki.gov.si/dataset/surs2164466s/resource/be163064-b1fd-4090-9bd1-72a4c6d1461b
- **PC-Axis file:** https://pxweb.stat.si/SiStatData/Resources/PX/Databases/Data/2164466S.PX
- **Format:** PC-Axis (.PX)
- **Provider:** Statistical Office of the Republic of Slovenia (SURS)
- **License:** Creative Commons Attribution 4.0 (CC BY 4.0)

The application is intended to retrieve the PC-Axis data dynamically from the online source when loaded, rather than relying on a manually downloaded dataset.

## Project Structure

```text
astro-destination/
├── src/
│   ├── __init__.py
│   ├── px_fetcher.py
│   ├── px_parser.py
│   └── tourism_service.py
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
│   └── __init__.py
├── main.py
├── requirements.txt
└── README.md
```

### Components

- **`src/px_fetcher.py`** – Retrieves PC-Axis data from the online source.
- **`src/px_parser.py`** – Parses PC-Axis files into structured data.
- **`src/tourism_service.py`** – Handles filtering, aggregation, comparisons, and statistical calculations.
- **`static/index.html`** – Defines the web interface.
- **`static/app.js`** – Handles user interactions and dynamic chart updates.
- **`static/styles.css`** – Defines the application styling.
- **`tests/`** – Contains automated tests.
- **`main.py`** – Application entry point.
- **`requirements.txt`** – Python dependencies.
