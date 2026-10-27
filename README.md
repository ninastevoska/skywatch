# SkyWatch

SkyWatch is an astronomy-focused project designed to help users plan sky observations by integrating astronomical events, observation locations, weather information, and destination insights.

The project is developed through independent, reusable modules that can later be integrated into a unified application.

## Project Structure

```text
skywatch/
├── astro-destination/  # Tourism statistics and destination insights
├── backend/            
├── data-model/         # XML and JSON data processing
├── docs/               
├── frontend/           
├── parser/             # NASA astronomy news scraper
└── README.md
```

## Modules

### Data Model

Processes and manages structured astronomical data using XML and JSON.

[View Data Model README](data-model/README.md)

### News Parser

Collects astronomy-related news from NASA through web scraping, validation, and JSON export.

[View Parser README](parser/README.md)

### AstroDestination Explorer

Analyzes official Slovenian tourism statistics using dynamically retrieved PC-Axis data. Provides interactive charts, municipality comparisons, and tourism trends to support astronomy trip planning.

[View AstroDestination README](astro-destination/README.md)
