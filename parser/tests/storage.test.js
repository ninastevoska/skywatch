const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const config = require("../src/config");
const {
  loadArticles,
  mergeArticles,
  saveArticles,
} = require("../src/storage");

function createArticle(id, publishedAt) {
  return {
    title: `Article ${id}`,
    published_at: publishedAt,
    summary: `Summary ${id}`,
    article_url: `https://www.nasa.gov/blogs/watch-the-skies/${id}/`,
    image_url: null,
    source: "NASA Watch the Skies",
  };
}

test("merges articles without duplicates", () => {
  const existing = [
    createArticle("article-1", "2025-01-01T00:00:00Z"),
  ];

  const incoming = [
    createArticle("article-1", "2025-01-01T00:00:00Z"),
    createArticle("article-2", "2025-02-01T00:00:00Z"),
  ];

  const merged = mergeArticles(existing, incoming);

  assert.equal(merged.length, 2);
  assert.equal(new Set(merged.map((a) => a.article_url)).size, 2);
});

test("updates an existing article when its URL matches", () => {
  const original = createArticle(
    "article-1",
    "2025-01-01T00:00:00Z"
  );

  const updated = {
    ...original,
    summary: "Updated summary",
  };

  const merged = mergeArticles([original], [updated]);

  assert.equal(merged.length, 1);
  assert.equal(merged[0].summary, "Updated summary");
});

test("sorts articles from newest to oldest", () => {
  const articles = [
    createArticle("old", "2023-01-01T00:00:00Z"),
    createArticle("new", "2025-01-01T00:00:00Z"),
    createArticle("middle", "2024-01-01T00:00:00Z"),
  ];

  const merged = mergeArticles([], articles);

  assert.deepEqual(
    merged.map((article) => article.title),
    ["Article new", "Article middle", "Article old"]
  );
});

test("returns an empty array when the output file does not exist", async () => {
  const originalPath = config.outputPath;
  const temporaryDirectory = await fs.mkdtemp(
    path.join(os.tmpdir(), "skywatch-test-")
  );

  try {
    config.outputPath = path.join(
      temporaryDirectory,
      "missing.json"
    );

    const articles = await loadArticles();

    assert.deepEqual(articles, []);
  } finally {
    config.outputPath = originalPath;
    await fs.rm(temporaryDirectory, {
      recursive: true,
      force: true,
    });
  }
});

test("saves and loads articles as JSON", async () => {
  const originalPath = config.outputPath;
  const temporaryDirectory = await fs.mkdtemp(
    path.join(os.tmpdir(), "skywatch-test-")
  );

  try {
    config.outputPath = path.join(
      temporaryDirectory,
      "output",
      "articles.json"
    );

    const articles = [
      createArticle("article-1", "2025-01-01T00:00:00Z"),
      createArticle("article-2", "2025-02-01T00:00:00Z"),
    ];

    await saveArticles(articles);

    const loaded = await loadArticles();

    assert.deepEqual(loaded, articles);

    const fileContent = await fs.readFile(
      config.outputPath,
      "utf8"
    );

    assert.deepEqual(JSON.parse(fileContent), articles);
  } finally {
    config.outputPath = originalPath;
    await fs.rm(temporaryDirectory, {
      recursive: true,
      force: true,
    });
  }
});

test("rejects stored data that is not an array", async () => {
  const originalPath = config.outputPath;
  const temporaryDirectory = await fs.mkdtemp(
    path.join(os.tmpdir(), "skywatch-test-")
  );

  try {
    config.outputPath = path.join(
      temporaryDirectory,
      "invalid.json"
    );

    await fs.writeFile(
      config.outputPath,
      JSON.stringify({ articles: [] }),
      "utf8"
    );

    await assert.rejects(
      loadArticles(),
      /Stored news data must be an array/
    );
  } finally {
    config.outputPath = originalPath;
    await fs.rm(temporaryDirectory, {
      recursive: true,
      force: true,
    });
  }
});
