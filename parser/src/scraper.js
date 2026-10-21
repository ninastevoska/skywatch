const puppeteer = require("puppeteer");
const config = require("./config");
const { extractArticles } = require("./extractor");

/**
 * Pauses execution between page requests.
 *
 * @param {number} milliseconds - Delay duration.
 * @returns {Promise<void>}
 */
function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

/**
 * Scrapes articles from the NASA Watch the Skies archive.
 *
 * @returns {Promise<Array<Object>>} Extracted articles.
 */
async function scrapeArticles() {
  const browser = await puppeteer.launch({
    headless: config.headless,
  });

  const articlesByUrl = new Map();

  try {
    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(config.navigationTimeoutMs);

    for (let pageNumber = 1; pageNumber <= config.maxPages; pageNumber++) {
      if (articlesByUrl.size >= config.maxArticles) {
        break;
      }

      const pageUrl = `${config.baseUrl}/page/${pageNumber}/`;

      console.log(`Scraping page ${pageNumber}: ${pageUrl}`);

      const response = await page.goto(pageUrl, {
        waitUntil: "domcontentloaded",
      });

      if (!response || !response.ok()) {
        throw new Error(
          `Failed to load page ${pageNumber}: HTTP ${response?.status() ?? "unknown"}`
        );
      }

      // Wait until the archive's article elements are available.
      await page.waitForSelector("article.nasa-blog", {
        timeout: config.navigationTimeoutMs,
      });

      const articles = await extractArticles(page);

      if (articles.length === 0) {
        console.log("No articles found. Stopping pagination.");
        break;
      }

      for (const article of articles) {
        if (article.article_url) {
          articlesByUrl.set(article.article_url, article);
        }

        if (articlesByUrl.size >= config.maxArticles) {
          break;
        }
      }

      console.log(
        `Found ${articles.length} articles (${articlesByUrl.size} unique total).`
      );

      if (
        pageNumber < config.maxPages &&
        articlesByUrl.size < config.maxArticles
      ) {
        await delay(config.requestDelayMs);
      }
    }
  } finally {
    await browser.close();
  }

  return [...articlesByUrl.values()];
}

module.exports = { scrapeArticles };
