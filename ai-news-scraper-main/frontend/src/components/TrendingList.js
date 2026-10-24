"use client";

import { useState } from "react";
import styles from "./TrendingList.module.css";

export default function TrendingList({ keywords = [], windowDays = null }) {
  const [showAll, setShowAll] = useState(false);
  const displayedKeywords = showAll ? keywords : keywords.slice(0, 5);
  const timeframeLabel = windowDays
    ? `Last ${windowDays} days`
    : "Recent window";

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>What's Trending</h3>
        <span className={styles.timeframe}>{timeframeLabel}</span>
      </div>

      <div className={styles.list}>
        {displayedKeywords.map((item, i) => (
          <div
            key={item.keyword}
            className={styles.item}
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <div className={styles.rank}>{i + 1}</div>
            <div className={styles.info}>
              <span className={styles.keyword}>{item.keyword}</span>
              <span className={styles.count}>
                {item.count ?? item.recent_count ?? 0} mentions
              </span>
            </div>
            {item.delta !== undefined && (
              <div
                className={`${styles.delta} ${item.delta >= 0 ? styles.positive : styles.negative}`}
              >
                {item.delta >= 0 ? "▲" : "▼"} {Math.abs(item.delta)}%
              </div>
            )}
          </div>
        ))}
      </div>

      {keywords.length > 5 && (
        <button
          className={styles.exploreBtn}
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? "Show Less" : "Explore All Trends"}
        </button>
      )}
    </div>
  );
}
