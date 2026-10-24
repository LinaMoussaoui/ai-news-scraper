"use client";

import { useMemo } from "react";
import styles from "./ArticleReader.module.css";

export default function ArticleReader({ article, onClose }) {
  const publishedDate = useMemo(() => {
    if (!article) return "";
    const date = new Date(article.published_date || article.scraped_at);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [article]);

  if (!article) {
    return (
      <div className={styles.emptyReader}>
        <div className={styles.emptyIcon}>READ</div>
        <h3>Select an article to read</h3>
        <p>
          Choose from the feed on the left to see the full details and
          analytics.
        </p>
      </div>
    );
  }

  return (
    <div className={`${styles.reader} animate-slide-right`}>
      <div className={styles.stickyHeader}>
        <button
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="Close reader"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <div className={styles.actions}>
          <button
            className={styles.actionBtn}
            title="Share"
            onClick={() => {
              if (navigator.share) {
                navigator
                  .share({
                    title: article.title,
                    text: article.description,
                    url: article.url,
                  })
                  .catch(console.error);
              } else {
                navigator.clipboard.writeText(article.url);
                alert("Link copied to clipboard!");
              }
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
              <polyline points="16 6 12 2 8 6" />
              <line x1="12" y1="2" x2="12" y2="15" />
            </svg>
          </button>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.meta}>
          <span className={styles.sourceTag}>{article.source}</span>
          <span className={styles.categoryTag}>{article.category}</span>
        </div>

        <h1 className={styles.title}>{article.title}</h1>

        <div className={styles.authorRow}>
          <div className={styles.avatar}>
            {article.author?.charAt(0) || "A"}
          </div>
          <div className={styles.authorInfo}>
            <span className={styles.authorName}>
              {article.author || "AI Research Team"}
            </span>
            <span className={styles.date}>{publishedDate}</span>
          </div>
        </div>

        <div className={styles.body}>
          {article.content ? (
            article.content
              .split("\n")
              .map((para, i) => para.trim() && <p key={i}>{para}</p>)
          ) : (
            <p className={styles.noContent}>
              No full content available for this article.
            </p>
          )}
        </div>

        {/* Tools/entities section removed */}

        <div className={styles.externalLink}>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.linkBtn}
          >
            Read Original Article
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}
