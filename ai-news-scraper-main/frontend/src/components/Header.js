"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import styles from "./Header.module.css";

export default function Header({
  onSearch,
  wsStatus,
  onRefresh,
  categoryOptions = [],
  sourceOptions = [],
}) {
  const [query, setQuery] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [filters, setFilters] = useState({
    source: "all",
    category: "all",
    days: "all",
  });
  const filterRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (filterRef.current && !filterRef.current.contains(e.target)) {
        setFilterOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (query === "") {
      onSearch?.("", filters);
      return;
    }

    const timer = setTimeout(() => {
      onSearch?.(query, filters);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, filters, onSearch]);

  const handleSearchChange = (e) => {
    setQuery(e.target.value);
  };

  const handleClearAll = () => {
    const resetFilters = { source: "all", category: "all", days: "all" };
    setQuery("");
    setFilters(resetFilters);
    onSearch?.("", resetFilters);
  };

  const statusColor =
    {
      connected: "var(--success)",
      connecting: "var(--warning)",
      disconnected: "var(--text-muted)",
      error: "var(--error)",
    }[wsStatus] || "var(--text-muted)";

  const statusLabel =
    {
      connected: "Live",
      connecting: "Connecting…",
      disconnected: "Offline",
      error: "Error",
    }[wsStatus] || "Offline";

  return (
    <header className={styles.header} role="banner">
      <div className={styles.left}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2L2 7L12 12L22 7L12 2Z"
                fill="var(--primary)"
                opacity="0.9"
              />
              <path
                d="M2 17L12 22L22 17"
                stroke="var(--primary)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M2 12L12 17L22 12"
                stroke="var(--primary-light)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div className={styles.logoText}>
            <span className={styles.logoTitle}>AI Trends</span>
            <span className={styles.logoDivider}>&</span>
            <span className={styles.logoTitle}>News</span>
          </div>
        </div>
      </div>

      <div className={styles.center}>
        <div className={styles.searchWrapper}>
          <svg
            className={styles.searchIcon}
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            id="search-input"
            className={styles.searchInput}
            type="search"
            placeholder="Search articles, keywords, tools…"
            value={query}
            onChange={handleSearchChange}
            aria-label="Search articles"
          />
          {query && (
            <button
              className={styles.searchClear}
              onClick={() => {
                setQuery("");
                onSearch?.("", filters);
              }}
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className={styles.filterContainer} ref={filterRef}>
          <button
            id="filter-toggle"
            className={`${styles.filterBtn} ${filterOpen ? styles.filterBtnActive : ""}`}
            onClick={() => setFilterOpen((p) => !p)}
            aria-expanded={filterOpen}
            aria-haspopup="true"
            aria-label="Open filters"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
            </svg>
            Filters
          </button>

          {filterOpen && (
            <div
              className={styles.filterDropdown}
              role="dialog"
              aria-label="Filter options"
            >
              <label className={styles.filterLabel}>
                Source
                <select
                  value={filters.source}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, source: e.target.value }))
                  }
                >
                  <option value="all">All Sources</option>
                  {sourceOptions.map((source) => (
                    <option key={source} value={source}>
                      {source}
                    </option>
                  ))}
                </select>
              </label>

              <label className={styles.filterLabel}>
                Category
                <select
                  value={filters.category}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, category: e.target.value }))
                  }
                >
                  <option value="all">All Categories</option>
                  {categoryOptions.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>

              <label className={styles.filterLabel}>
                Time Range
                <select
                  value={filters.days}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      days:
                        e.target.value === "all"
                          ? "all"
                          : parseInt(e.target.value, 10),
                    }))
                  }
                >
                  <option value="all">All time</option>
                  <option value={7}>Last 7 days</option>
                  <option value={14}>Last 14 days</option>
                  <option value={30}>Last 30 days</option>
                </select>
              </label>

              <button
                type="button"
                className={styles.filterClearBtn}
                onClick={handleClearAll}
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      </div>

      <div className={styles.right}>
        <Link href="/articles" className={styles.articlesLink}>
          All Articles
        </Link>
        <div className={styles.wsStatus} title={`WebSocket: ${statusLabel}`}>
          <span
            className={styles.statusDot}
            style={{ background: statusColor }}
          />
          <span className={styles.statusText}>{statusLabel}</span>
        </div>
        <button
          id="refresh-btn"
          className={styles.refreshBtn}
          onClick={onRefresh}
          aria-label="Refresh data"
          title="Refresh data"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>
    </header>
  );
}
