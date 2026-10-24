"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import Header from "@/components/Header";
import KPICards from "@/components/KPICards";
import {
  ArticlesPerDayChart,
  SourceDistributionChart,
  CategoryChart,
} from "@/components/AnalyticsCharts";
import ArticleFeed from "@/components/ArticleFeed";
import ArticleReader from "@/components/ArticleReader";
import TrendingList from "@/components/TrendingList";
import useWebSocket from "@/lib/useWebSocket";
import { fetchDashboardData, getTrends } from "@/lib/api";
import styles from "./page.module.css";

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [articles, setArticles] = useState([]);
  const [trends, setTrends] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const articlesPerPage = 12;
  const [activeFilters, setActiveFilters] = useState({
    source: "all",
    category: "all",
    days: "all",
  });

  const categoryOptions = useMemo(() => {
    const values = [
      ...(articles || []).map((article) => article.category),
      ...(trends?.categories || []).map((entry) => entry.category),
    ];

    return [
      ...new Set(
        values
          .filter(Boolean)
          .map((value) => String(value).trim())
          .filter(Boolean),
      ),
    ].sort((a, b) => a.localeCompare(b));
  }, [articles, trends]);

  const sourceOptions = useMemo(() => {
    const values = [
      ...(articles || []).map((article) => article.source),
      ...(trends?.sources || []).map((entry) => entry.source),
    ];

    return [
      ...new Set(
        values
          .filter(Boolean)
          .map((value) => String(value).trim())
          .filter(Boolean),
      ),
    ].sort((a, b) => a.localeCompare(b));
  }, [articles, trends]);

  // WebSocket for real-time updates
  const { status: wsStatus } = useWebSocket("events", (event) => {
    console.log("WS Event:", event);
    if (event.type === "article_added" || event.type === "articles_batch") {
      const newArticles = Array.isArray(event.data) ? event.data : [event.data];
      setArticles((prev) => [...newArticles, ...prev].slice(0, 200));

      // Update KPIs optimistically if it's a simple count
      setKpis((prev) =>
        prev
          ? { ...prev, totalArticles: prev.totalArticles + newArticles.length }
          : null,
      );
    }
    if (event.type === "analytics_generated") {
      setTrends(event.data.trends);
    }
  });

  const loadData = useCallback(async (isRefresh = false, days = "all") => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const trendDays = days === "all" ? 7 : days;
      const articleDays = days === "all" ? null : days;
      const data = await fetchDashboardData(trendDays, articleDays);

      setArticles(data.articles || []);
      setTrends(data.trends);
      setKpis({
        totalArticles: data.articles?.length || 0,
        trendingKeywords: data.trends?.keywords?.length || 0,
        activeSources: data.trends?.sources?.length || 0,
      });
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData(false, activeFilters.days);
  }, [loadData, activeFilters.days]);

  const handleSearch = (query, filters) => {
    setSearchQuery(query);
    setActiveFilters(filters);
  };

  const filteredArticles = useMemo(() => {
    const normalize = (value) =>
      String(value || "")
        .trim()
        .toLowerCase();

    return articles.filter((art) => {
      const matchesSearch =
        !searchQuery ||
        art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.keywords?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSource =
        activeFilters.source === "all" ||
        normalize(art.source) === normalize(activeFilters.source);
      const matchesCategory =
        activeFilters.category === "all" ||
        normalize(art.category) === normalize(activeFilters.category);

      return matchesSearch && matchesSource && matchesCategory;
    });
  }, [articles, searchQuery, activeFilters]);

  return (
    <div
      className={`${styles.dashboard} ${selectedArticle ? styles.withReader : ""}`}
    >
      <Header
        onSearch={handleSearch}
        wsStatus={wsStatus}
        onRefresh={() => loadData(true, activeFilters.days)}
        categoryOptions={categoryOptions}
        sourceOptions={sourceOptions}
      />

      <aside className={styles.leftPane}>
        <ArticleFeed
          articles={filteredArticles}
          activeId={selectedArticle?.article_id}
          onSelect={setSelectedArticle}
          pageSize={articlesPerPage}
          totalItems={filteredArticles.length}
        />
      </aside>

      <main className={styles.mainArea}>
        <div className={styles.scrollContent}>
          <div className={styles.contentHeader}>
            <div className={styles.titleGroup}>
              <h1>Analytics Overview</h1>
              <p className={styles.subtitle}>
                AI news and trends for researchers and students.
              </p>
            </div>
            {refreshing && <div className={styles.loader}>Refreshing...</div>}
          </div>

          <KPICards data={kpis} loading={loading} />

          <div className={styles.chartsGrid}>
            <div className={styles.span2}>
              <ArticlesPerDayChart data={trends?.trends || []} />
            </div>
            <SourceDistributionChart data={trends?.sources || []} />
            <CategoryChart data={trends?.categories || []} />
            {/* Tools & Frameworks removed */}
            <TrendingList
              keywords={trends?.keywords || []}
              windowDays={trends?.window_days}
            />
          </div>

          <footer className={styles.footer}>
            <p>
              © 2026 AI Trends & News Scraper. Built for AI Students &
              Researchers.
            </p>
            <div className={styles.footerLinks}>
              <Link href="/articles">All Articles</Link>
              <a href="#">API Reference</a>
              <a href="#">Accessibility</a>
            </div>
          </footer>
        </div>
      </main>

      {selectedArticle && (
        <aside className={styles.rightPane}>
          <ArticleReader
            article={selectedArticle}
            onClose={() => setSelectedArticle(null)}
          />
        </aside>
      )}
    </div>
  );
}
