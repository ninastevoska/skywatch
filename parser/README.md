# SkyWatch News Parser

A web scraper developed for the **SkyWatch** astronomy observation planning project.

The parser uses **Node.js and Puppeteer** to collect astronomy-related news from [NASA Watch the Skies](https://www.nasa.gov/blogs/watch-the-skies/).

It extracts article titles, publication dates, summaries, article URLs, and image URLs. The collected data is validated, sorted by publication date, and saved in JSON format. Existing articles are updated without creating duplicates.

## Installation

**Requirements:** Node.js and npm.

Navigate to the `parser` directory and install the dependencies:

```bash
cd parser
npm install
```

## Usage

Run the parser:

```bash
node index.js
```

The collected articles are saved to:

```text
output/astronomy_news.json
```

By default, the parser collects up to **100 articles** from the NASA blog archive.

## Testing

Run all automated tests:

```bash
node --test
```

The tests cover HTML extraction, data validation, and JSON storage.
