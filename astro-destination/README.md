# AstroDestination Explorer

AstroDestination Explorer is a standalone module of the **SkyWatch** project that helps users explore tourism activity in Slovenian municipalities when planning astronomy-related trips.

The application dynamically retrieves official tourism statistics in PC-Axis format, processes them, and presents the results through interactive charts. It is designed for future integration into SkyWatch as an **About Destination** section.

## Features

- **Monthly overnight stays:** View monthly tourism activity for a selected municipality and year.
- **Destination comparison:** Compare monthly overnight stays between two municipalities.
- **Busiest and quietest months:** Identify months with the highest and lowest overnight stays.
- **Yearly trends:** Explore tourism trends across available years, including incomplete-year indicators.

## Technologies

- **Backend:** Python, FastAPI, Pandas, Pyaxis
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Testing:** unittest, FastAPI TestClient

## Data Source

Tourism statistics are provided by the **Statistical Office of the Republic of Slovenia (SURS)** through the Slovenian Open Data Portal (OPSI).

- **Dataset:** [Tourist arrivals and overnight stays by municipality](https://podatki.gov.si/dataset/surs2164466s)
- **PC-Axis source:** [2164466S.PX](https://pxweb.stat.si/SiStatData/Resources/PX/Databases/Data/2164466S.PX)
- **Format:** PC-Axis (.PX)
- **License:** Creative Commons Attribution 4.0 (CC BY 4.0)

Data is retrieved automatically when the backend starts. Statistics are based on tourist overnight stays across all countries of origin. Missing months are not treated as zero.

## Installation and Usage

Requires Python 3.10+ and an internet connection for the initial data download.

From the `astro-destination` directory:

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/** to use the dashboard.

API documentation is available at **http://127.0.0.1:8000/docs**.

## Testing

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

The test suite contains **36 tests** covering data retrieval, parsing, statistical calculations, and API endpoints.

## Project Structure

```text
astro-destination/
├── src/
│   ├── px_fetcher.py
│   ├── px_parser.py
│   └── tourism_service.py
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
│   ├── test_px_fetcher.py
│   ├── test_px_parser.py
│   ├── test_tourism_service.py
│   └── test_api.py
├── main.py
├── requirements.txt
└── README.md
```
