const path = require("node:path");

const config = {
  baseUrl: "https://www.nasa.gov/blogs/watch-the-skies",
  sourceName: "NASA Watch the Skies",

  maxArticles: 100,
  maxPages: 15,

  navigationTimeoutMs: 30000,
  requestDelayMs: 1500,

  headless: true,

  outputPath: path.join(
    __dirname,
    "..",
    "output",
    "astronomy_news.json"
  ),
};

module.exports = config;
