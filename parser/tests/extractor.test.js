const test = require("node:test");
const assert = require("node:assert/strict");
const puppeteer = require("puppeteer");

const { extractArticles } = require("../src/extractor");

test("extracts article information from HTML", async () => {
  const browser = await puppeteer.launch({ headless: true });

  try {
    const page = await browser.newPage();

    await page.setContent(`
      <article class="nasa-blog">
        <a href="https://www.nasa.gov/blogs/watch-the-skies/example/">
          <img src="https://www.nasa.gov/example.jpg" alt="Astronomy">
          <h2>Example Astronomy Article</h2>
        </a>

        <time datetime="2026-10-05T20:10:05+00:00">
          October 5, 2026
        </time>

        <div class="blog-excerpt">
          <p>Learn more about the night sky.</p>
        </div>
      </article>
    `);

    const articles = await extractArticles(page);

    assert.equal(articles.length, 1);

    assert.deepEqual(articles[0], {
      title: "Example Astronomy Article",
      published_at: "2026-10-05T20:10:05+00:00",
      summary: "Learn more about the night sky.",
      article_url:
        "https://www.nasa.gov/blogs/watch-the-skies/example/",
      image_url: "https://www.nasa.gov/example.jpg",
    });
  } finally {
    await browser.close();
  }
});

test("handles missing optional article fields", async () => {
  const browser = await puppeteer.launch({ headless: true });

  try {
    const page = await browser.newPage();

    await page.setContent(`
      <article class="nasa-blog">
        <a href="https://www.nasa.gov/blogs/watch-the-skies/example/">
          <h2>Article Without Image or Summary</h2>
        </a>

        <time datetime="2026-09-15T12:00:00+00:00">
          September 15, 2026
        </time>
      </article>
    `);

    const articles = await extractArticles(page);

    assert.equal(articles.length, 1);
    assert.equal(
      articles[0].title,
      "Article Without Image or Summary"
    );
    assert.equal(articles[0].summary, null);
    assert.equal(articles[0].image_url, null);
  } finally {
    await browser.close();
  }
});

test("returns an empty array when no articles are present", async () => {
  const browser = await puppeteer.launch({ headless: true });

  try {
    const page = await browser.newPage();

    await page.setContent("<main>No articles found</main>");

    const articles = await extractArticles(page);

    assert.deepEqual(articles, []);
  } finally {
    await browser.close();
  }
});
