const config = require("./config");

/**
 * Normalizes whitespace in a text value.
 *
 * @param {string|null} value - Text to normalize.
 * @returns {string|null} Normalized text.
 */
function normalizeText(value) {
  if (typeof value !== "string") {
    return null;
  }

  return value.replace(/\s+/g, " ").trim() || null;
}

/**
 * Validates and normalizes an article URL.
 *
 * @param {string|null} value - Article URL.
 * @returns {string|null} Normalized URL.
 */
function normalizeArticleUrl(value) {
  if (typeof value !== "string") {
    return null;
  }

  try {
    const url = new URL(value.trim());

    if (
      url.protocol !== "https:" ||
      url.hostname !== "www.nasa.gov" ||
      !url.pathname.startsWith("/blogs/watch-the-skies/")
    ) {
      return null;
    }

    url.hash = "";
    url.search = "";

    return url.toString();
  } catch {
    return null;
  }
}

/**
 * Validates a URL used for an article image.
 *
 * @param {string|null} value - Image URL.
 * @returns {string|null} Validated URL.
 */
function normalizeImageUrl(value) {
  if (typeof value !== "string") {
    return null;
  }

  try {
    const url = new URL(value.trim());

    if (url.protocol !== "https:") {
      return null;
    }

    return url.toString();
  } catch {
    return null;
  }
}

/**
 * Validates and normalizes an extracted article.
 *
 * @param {Object} article - Raw article data.
 * @returns {Object|null} Validated article or null.
 */
function validateArticle(article) {
  if (!article || typeof article !== "object") {
    return null;
  }

  const title = normalizeText(article.title);
  const summary = normalizeText(article.summary);
  const articleUrl = normalizeArticleUrl(article.article_url);
  const imageUrl = normalizeImageUrl(article.image_url);

  const publishedAt = article.published_at;
  const timestamp = Date.parse(publishedAt);

  // Required fields must be valid before storing the article.
  if (!title || !articleUrl || !Number.isFinite(timestamp)) {
    return null;
  }

  // Ignore articles dated in the future.
  if (timestamp > Date.now()) {
    return null;
  }

  return {
    title,
    published_at: new Date(timestamp).toISOString(),
    summary,
    article_url: articleUrl,
    image_url: imageUrl,
    source: config.sourceName,
  };
}

module.exports = {
  validateArticle,
  normalizeText,
  normalizeArticleUrl,
  normalizeImageUrl,
};
