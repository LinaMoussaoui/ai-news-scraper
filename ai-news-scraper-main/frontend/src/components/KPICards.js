"use client";

import styles from "./KPICards.module.css";

const icons = {
  articles: (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  ),
  keywords: (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  sources: (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  ),
  tools: (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  ),
};

const colorSchemes = {
  articles: {
    bg: "var(--primary-ghost)",
    color: "var(--primary)",
    gradient: "linear-gradient(135deg, #1a56db15, #3b82f610)",
  },
  keywords: {
    bg: "var(--accent-ghost)",
    color: "var(--accent)",
    gradient: "linear-gradient(135deg, #7c3aed15, #a78bfa10)",
  },
  sources: {
    bg: "var(--success-ghost)",
    color: "var(--success)",
    gradient: "linear-gradient(135deg, #05966915, #10b98110)",
  },
  tools: {
    bg: "var(--warning-ghost)",
    color: "var(--warning)",
    gradient: "linear-gradient(135deg, #d9770615, #f59e0b10)",
  },
};

function KPICard({ type, label, value, subtitle, loading }) {
  const scheme = colorSchemes[type];
  return (
    <div
      className={`${styles.card} animate-fade-in-up`}
      style={{ background: scheme.gradient }}
    >
      <div className={styles.cardHeader}>
        <div
          className={styles.iconWrap}
          style={{ background: scheme.bg, color: scheme.color }}
        >
          {icons[type]}
        </div>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.valueRow}>
        {loading ? (
          <div className={`${styles.skeleton} animate-shimmer`} />
        ) : (
          <span className={styles.value} style={{ color: scheme.color }}>
            {typeof value === "number" ? value.toLocaleString() : value}
          </span>
        )}
      </div>
      {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
    </div>
  );
}

export default function KPICards({ data, loading }) {
  const cards = [
    {
      type: "articles",
      label: "Total Articles",
      value: data?.totalArticles ?? 0,
      subtitle: "Live feed total",
    },
    {
      type: "keywords",
      label: "Trending Keywords",
      value: data?.trendingKeywords ?? 0,
      subtitle: "This week",
    },
    {
      type: "sources",
      label: "Active Sources",
      value: data?.activeSources ?? 0,
      subtitle: "Feeds monitored",
    },
  ];

  // Hide tools KPI when dataset is small
  // Tools & Frameworks KPI removed

  return (
    <section className={styles.grid} aria-label="Key performance indicators">
      {cards.map((card, i) => (
        <KPICard key={card.type} {...card} loading={loading} />
      ))}
    </section>
  );
}
