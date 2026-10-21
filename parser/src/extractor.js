/**
 * Extracts astronomy news articles from a NASA blog archive page.
 *
 * @param {import("puppeteer").Page} page - Puppeteer page instance.
 * @returns {Promise<Array<Object>>} Extracted article data.
 */
async function extractArticles(page) {
  return page.$$eval("article.nasa-blog", (elements) =>
    elements.map((article) => {
      const titleElement = article.querySelector("h2");
      const dateElement = article.querySelector("time[datetime]");
      const linkElement = article.querySelector("a:has(h2)");
      const summaryElement = article.querySelector(".blog-excerpt p");
      const imageElement = linkElement?.querySelector("img");

      return {
        title: titleElement?.textContent.trim() || null,
        published_at: dateElement?.getAttribute("datetime") || null,
        summary: summaryElement?.innerText.trim() || null,
        article_url: linkElement?.href || null,
        image_url: imageElement?.src || null,
      };
    })
  );
}

module.exports = { extractArticles };
