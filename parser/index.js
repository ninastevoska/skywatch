const config = require("./src/config");
const { scrapeArticles } = require("./src/scraper");
const { validateArticle } = require("./src/validator");
const {
  loadArticles,
  mergeArticles,
  saveArticles,
} = require("./src/storage");

/**
 * Runs the NASA astronomy news scraping pipeline.
 *
 * @returns {Promise<void>}
 */
async function main() {
  console.log("Starting SkyWatch News Parser...\n");

  // Fetch articles from the NASA archive.
  const scrapedArticles = await scrapeArticles();

  // Validate and normalize extracted articles.
  const validArticles = scrapedArticles
    .map(validateArticle)
    .filter((article) => article !== null);

  if (validArticles.length === 0) {
    throw new Error("No valid articles were extracted. Existing data was preserved.");
  }

  // Load existing data and identify newly discovered articles.
  const existingArticles = await loadArticles();

  const existingUrls = new Set(
    existingArticles.map((article) => article.article_url)
  );

  const newArticleCount = validArticles.filter(
    (article) => !existingUrls.has(article.article_url)
  ).length;

  // Merge, deduplicate, and persist articles.
  const mergedArticles = mergeArticles(existingArticles, validArticles);

  await saveArticles(mergedArticles);

  console.log("\nSkyWatch News Parser completed successfully.");
  console.log(`Source: ${config.sourceName}`);
  console.log(`Scraped articles: ${scrapedArticles.length}`);
  console.log(`Valid articles: ${validArticles.length}`);
  console.log(`New articles: ${newArticleCount}`);
  console.log(`Total stored articles: ${mergedArticles.length}`);
  console.log(`Output: ${config.outputPath}`);
}

// Report failures without overwriting previously stored data.
main().catch((error) => {
  console.error(`\nParser failed: ${error.message}`);
  process.exitCode = 1;
});
