const test = require("node:test");
const assert = require("node:assert/strict");

const {
  validateArticle,
  normalizeText,
  normalizeArticleUrl,
  normalizeImageUrl,
} = require("../src/validator");

const validArticle = {
  title: "  Meteor   Shower  ",
  published_at: "2025-08-05T19:37:23+00:00",
  summary: "  Watch   the night\nsky.  ",
  article_url:
    "https://www.nasa.gov/blogs/watch-the-skies/example/",
  image_url: "https://www.nasa.gov/example.jpg",
};

test("normalizes whitespace in text", () => {
  assert.equal(normalizeText("  Hello   world\n"), "Hello world");
  assert.equal(normalizeText("   "), null);
  assert.equal(normalizeText(null), null);
});

test("accepts valid NASA article URLs", () => {
  assert.equal(
    normalizeArticleUrl(
      "https://www.nasa.gov/blogs/watch-the-skies/example/?ref=test#section"
    ),
    "https://www.nasa.gov/blogs/watch-the-skies/example/"
  );
});

test("rejects invalid article URLs", () => {
  assert.equal(normalizeArticleUrl("https://example.com/article"), null);
  assert.equal(
    normalizeArticleUrl("http://www.nasa.gov/blogs/watch-the-skies/example/"),
    null
  );
  assert.equal(normalizeArticleUrl("invalid-url"), null);
});

test("validates image URLs", () => {
  assert.equal(
    normalizeImageUrl("https://www.nasa.gov/image.jpg"),
    "https://www.nasa.gov/image.jpg"
  );
  assert.equal(normalizeImageUrl("http://example.com/image.jpg"), null);
  assert.equal(normalizeImageUrl(null), null);
});

test("validates and normalizes a complete article", () => {
  const article = validateArticle(validArticle);

  assert.deepEqual(article, {
    title: "Meteor Shower",
    published_at: "2025-08-05T19:37:23.000Z",
    summary: "Watch the night sky.",
    article_url:
      "https://www.nasa.gov/blogs/watch-the-skies/example/",
    image_url: "https://www.nasa.gov/example.jpg",
    source: "NASA Watch the Skies",
  });
});

test("accepts missing optional fields", () => {
  const article = validateArticle({
    ...validArticle,
    summary: null,
    image_url: null,
  });

  assert.equal(article.summary, null);
  assert.equal(article.image_url, null);
});

test("rejects missing required fields", () => {
  assert.equal(
    validateArticle({ ...validArticle, title: null }),
    null
  );
  assert.equal(
    validateArticle({ ...validArticle, article_url: null }),
    null
  );
  assert.equal(
    validateArticle({ ...validArticle, published_at: null }),
    null
  );
});

test("rejects invalid or future publication dates", () => {
  assert.equal(
    validateArticle({ ...validArticle, published_at: "invalid-date" }),
    null
  );

  assert.equal(
    validateArticle({
      ...validArticle,
      published_at: "2099-01-01T00:00:00Z",
    }),
    null
  );
});
