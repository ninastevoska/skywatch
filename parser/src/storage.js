const fs = require("node:fs/promises");
const path = require("node:path");
const config = require("./config");

/**
 * Loads previously saved articles from a JSON file.
 *
 * @returns {Promise<Array<Object>>} Previously stored articles.
 */
async function loadArticles() {
  try {
    const content = await fs.readFile(config.outputPath, "utf8");
    const data = JSON.parse(content);

    if (!Array.isArray(data)) {
      throw new Error("Stored news data must be an array.");
    }

    return data;
  } catch (error) {
    if (error.code === "ENOENT") {
      return [];
    }

    throw error;
  }
}

/**
 * Merges existing and newly extracted articles.
 * Articles are uniquely identified by their URLs.
 *
 * @param {Array<Object>} existingArticles - Previously stored articles.
 * @param {Array<Object>} newArticles - Newly extracted articles.
 * @returns {Array<Object>} Merged articles.
 */
function mergeArticles(existingArticles, newArticles) {
  const articlesByUrl = new Map();

  for (const article of existingArticles) {
    articlesByUrl.set(article.article_url, article);
  }

  // Replace existing records with their latest validated versions.
  for (const article of newArticles) {
    articlesByUrl.set(article.article_url, article);
  }

  return [...articlesByUrl.values()].sort(
    (a, b) => Date.parse(b.published_at) - Date.parse(a.published_at)
  );
}

/**
 * Saves articles to JSON using a temporary file.
 * The existing file is replaced only after writing succeeds.
 *
 * @param {Array<Object>} articles - Articles to save.
 * @returns {Promise<void>}
 */
async function saveArticles(articles) {
  const outputDirectory = path.dirname(config.outputPath);
  const temporaryPath = `${config.outputPath}.tmp`;

  await fs.mkdir(outputDirectory, { recursive: true });

  try {
    const content = JSON.stringify(articles, null, 2);

    await fs.writeFile(temporaryPath, `${content}\n`, "utf8");
    await fs.rename(temporaryPath, config.outputPath);
  } catch (error) {
    await fs.rm(temporaryPath, { force: true }).catch(() => {});
    throw error;
  }
}

module.exports = {
  loadArticles,
  mergeArticles,
  saveArticles,
};
