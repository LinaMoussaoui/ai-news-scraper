"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./ArticleFeed.module.css";

function ArticleCard({ article, isActive, onClick }) {
  const publishedDate = useMemo(() => {
    const date = new Date(article.published_date || article.scraped_at);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [article.published_date, article.scraped_at]);

  const tags = useMemo(() => {
    if (article.tags) return article.tags;
    if (article.keywords)
      return article.keywords
        .split(",")
        .map((k) => k.trim())
        .slice(0, 3);
    return [];
  }, [article.tags, article.keywords]);

  return (
    <article
      className={`${styles.card} ${isActive ? styles.active : ""} animate-fade-in`}
      onClick={() => onClick(article)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick(article)}
      aria-current={isActive ? "true" : "false"}
    >
      <div className={styles.cardHeader}>
        <span className={styles.source}>{article.source}</span>
        <time className={styles.time}>{publishedDate}</time>
      </div>
      <h3 className={styles.title}>{article.title}</h3>
      <p className={styles.snippet}>
        {article.description ||
          `${article.content?.substring(0, 120) || ""}...`}
      </p>

      <div className={styles.footer}>
        <div className={styles.tags}>
          {tags.map((tag) => (
            <span key={tag} className={styles.tag}>
              #{tag}
            </span>
          ))}
        </div>
        <div className={styles.metrics}>
          {article.read_count > 0 && (
            <span className={styles.metric}>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              {article.read_count}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

export default function ArticleFeed({
  articles = [],
  activeId,
  onSelect,
  pageSize = 12,
  totalItems,
}) {
  const [page, setPage] = useState(1);
  const safeTotal = totalItems ?? articles.length;
  const pageCount = Math.max(1, Math.ceil(safeTotal / pageSize));
  const start = safeTotal === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, safeTotal);
  const visibleArticles =
    articles.length > pageSize
      ? articles.slice((page - 1) * pageSize, page * pageSize)
      : articles;

  useEffect(() => {
    setPage((currentPage) => Math.min(currentPage, pageCount));
  }, [pageCount]);

  return (
    <div className={styles.feedWrapper}>
      <div className={styles.feedHeader}>
        <h2 className={styles.feedTitle}>Live Feed</h2>
        <span className={styles.count}>{safeTotal} total</span>
      </div>
      <div className={styles.list}>
        {visibleArticles.length > 0 ? (
          visibleArticles.map((article, i) => (
            <ArticleCard
              key={article.article_id || i}
              article={article}
              isActive={activeId === article.article_id}
              onClick={onSelect}
            />
          ))
        ) : (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>LIVE</div>
            <p>Waiting for live stream...</p>
          </div>
        )}
      </div>

      {pageCount > 1 && (
        <div className={styles.pagination}>
          <div className={styles.pageMeta}>
            Showing {start}-{end} of {safeTotal}
          </div>
          <div className={styles.pageControls}>
            <button
              type="button"
              className={styles.pageBtn}
              onClick={() =>
                setPage((currentPage) => Math.max(1, currentPage - 1))
              }
              disabled={page <= 1}
            >
              Prev
            </button>
            <span className={styles.pageIndicator}>
              {page} / {pageCount}
            </span>
            <button
              type="button"
              className={styles.pageBtn}
              onClick={() =>
                setPage((currentPage) => Math.min(pageCount, currentPage + 1))
              }
              disabled={page >= pageCount}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
