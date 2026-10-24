"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ArticleReader from "@/components/ArticleReader";
import { getArticles } from "@/lib/api";
import feedStyles from "@/components/ArticleFeed.module.css";
import styles from "./page.module.css";

const PAGE_SIZE = 12;

function ArticleCard({ article, isSelected, onSelect }) {
  const publishedDate = useMemo(() => {
    const date = new Date(article.published_date || article.scraped_at);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [article.published_date, article.scraped_at]);

  const tags = useMemo(() => {
    if (article.tags) return article.tags;
    if (article.keywords) {
      return article.keywords
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean)
        .slice(0, 3);
    }
    return [];
  }, [article.tags, article.keywords]);

  return (
    <article
      className={`${feedStyles.card} ${isSelected ? feedStyles.active : ""} ${styles.blogCard}`}
      onClick={() => onSelect(article)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect(article)}
      aria-current={isSelected ? "true" : "false"}
    >
      <div className={feedStyles.cardHeader}>
        <span className={feedStyles.source}>{article.source}</span>
        <time className={feedStyles.time}>{publishedDate}</time>
      </div>
      <h3 className={styles.blogTitle}>{article.title}</h3>
      <p className={styles.blogSnippet}>
        {article.description ||
          `${article.content?.substring(0, 220) || ""}...`}
      </p>

      <div className={feedStyles.footer}>
        <div className={feedStyles.tags}>
          {tags.map((tag) => (
            <span key={tag} className={feedStyles.tag}>
              #{tag}
            </span>
          ))}
        </div>
        <span className={styles.readMore}>Read article</span>
      </div>
    </article>
  );
}

export default function ArticlesPage() {
  const [loading, setLoading] = useState(true);
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({ source: "all", category: "all" });

  const loadArticles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getArticles(1000);
      const items = data?.articles || [];
      setArticles(items);
      setSelectedArticle(items[0] || null);
      setCurrentPage(1);
    } catch (error) {
      console.error("Failed to load articles page:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadArticles();
  }, [loadArticles]);

  const sourceOptions = useMemo(
    () =>
      [
        ...new Set(articles.map((article) => article.source).filter(Boolean)),
      ].sort((a, b) => a.localeCompare(b)),
    [articles],
  );

  const categoryOptions = useMemo(
    () =>
      [
        ...new Set(articles.map((article) => article.category).filter(Boolean)),
      ].sort((a, b) => a.localeCompare(b)),
    [articles],
  );

  const filteredArticles = useMemo(() => {
    const normalize = (value) =>
      String(value || "")
        .trim()
        .toLowerCase();
    const query = searchQuery.trim().toLowerCase();

    return articles.filter((article) => {
      const matchesSearch =
        !query ||
        article.title?.toLowerCase().includes(query) ||
        article.description?.toLowerCase().includes(query) ||
        article.content?.toLowerCase().includes(query) ||
        article.keywords?.toLowerCase().includes(query);

      const matchesSource =
        filters.source === "all" ||
        normalize(article.source) === normalize(filters.source);
      const matchesCategory =
        filters.category === "all" ||
        normalize(article.category) === normalize(filters.category);

      return matchesSearch && matchesSource && matchesCategory;
    });
  }, [articles, searchQuery, filters]);

  const pageCount = Math.max(1, Math.ceil(filteredArticles.length / PAGE_SIZE));
  const visibleArticles = filteredArticles.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  useEffect(() => {
    setCurrentPage((page) => Math.min(page, pageCount));
  }, [pageCount]);

  return (
    <div className={styles.pageShell}>
      <header className={styles.hero}>
        <div>
          <Link href="/" className={styles.backLink}>
            Back to dashboard
          </Link>
          <h1>All Articles</h1>
          <p>
            A paginated archive of the latest AI, data science, and research
            posts.
          </p>
        </div>

        <div className={styles.heroMeta}>
          <div>
            <span className={styles.metaLabel}>Articles</span>
            <strong>{filteredArticles.length.toLocaleString()}</strong>
          </div>
          <div>
            <span className={styles.metaLabel}>Pages</span>
            <strong>{pageCount.toLocaleString()}</strong>
          </div>
        </div>
      </header>

      <section className={styles.toolbar}>
        <input
          type="search"
          placeholder="Search articles, authors, topics, and tools"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setCurrentPage(1);
          }}
          className={styles.searchInput}
        />

        <select
          value={filters.source}
          onChange={(e) => {
            setFilters((prev) => ({ ...prev, source: e.target.value }));
            setCurrentPage(1);
          }}
          className={styles.select}
        >
          <option value="all">All sources</option>
          {sourceOptions.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>

        <select
          value={filters.category}
          onChange={(e) => {
            setFilters((prev) => ({ ...prev, category: e.target.value }));
            setCurrentPage(1);
          }}
          className={styles.select}
        >
          <option value="all">All categories</option>
          {categoryOptions.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>

        <button
          type="button"
          className={styles.refreshBtn}
          onClick={loadArticles}
        >
          Refresh
        </button>
      </section>

      <main className={styles.content}>
        <section className={styles.listPane}>
          <div className={styles.listHeader}>
            <h2>Recent posts</h2>
            <span>
              {loading ? "Loading..." : `${visibleArticles.length} shown`}
            </span>
          </div>

          <div className={styles.cardGrid}>
            {visibleArticles.length > 0 ? (
              visibleArticles.map((article) => (
                <ArticleCard
                  key={article.article_id}
                  article={article}
                  isSelected={
                    selectedArticle?.article_id === article.article_id
                  }
                  onSelect={setSelectedArticle}
                />
              ))
            ) : (
              <div className={styles.emptyState}>
                No articles match the current filters.
              </div>
            )}
          </div>

          {pageCount > 1 && (
            <div className={styles.pagination}>
              <button
                type="button"
                className={styles.pageBtn}
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                disabled={currentPage <= 1}
              >
                Prev
              </button>
              <span>
                Page {currentPage} of {pageCount}
              </span>
              <button
                type="button"
                className={styles.pageBtn}
                onClick={() =>
                  setCurrentPage((page) => Math.min(pageCount, page + 1))
                }
                disabled={currentPage >= pageCount}
              >
                Next
              </button>
            </div>
          )}
        </section>

        <aside className={styles.readerPane}>
          <ArticleReader
            article={selectedArticle}
            onClose={() => setSelectedArticle(null)}
          />
        </aside>
      </main>
    </div>
  );
}
