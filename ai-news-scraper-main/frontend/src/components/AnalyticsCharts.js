"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";
import styles from "./AnalyticsCharts.module.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const chartColors = [
  "#1a56db",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#dc2626",
  "#0284c7",
  "#db2777",
  "#65a30d",
  "#ea580c",
  "#6366f1",
];

/* ---------- Articles per Day (Line Chart) ---------- */
export function ArticlesPerDayChart({ data = [] }) {
  const chartData = useMemo(
    () => ({
      labels: data.map((d) => {
        const date = new Date(d.date);
        return date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });
      }),
      datasets: [
        {
          label: "Articles",
          data: data.map((d) => d.count),
          borderColor: "#1a56db",
          backgroundColor: "rgba(26, 86, 219, 0.08)",
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#1a56db",
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
        },
      ],
    }),
    [data],
  );

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#111827",
        titleFont: { family: "Inter", size: 12 },
        bodyFont: { family: "Inter", size: 11 },
        padding: 10,
        cornerRadius: 8,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { font: { family: "Inter", size: 11 }, color: "#9ca3af" },
      },
      y: {
        beginAtZero: true,
        grid: { color: "#f3f4f6" },
        ticks: {
          font: { family: "Inter", size: 11 },
          color: "#9ca3af",
          stepSize: 5,
        },
      },
    },
    interaction: { intersect: false, mode: "index" },
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Articles per Day</h3>
        <span className={styles.chartBadge}>7 days</span>
      </div>
      <div className={styles.chartBody}>
        {data.length > 0 ? (
          <Line data={chartData} options={options} />
        ) : (
          <div className={styles.empty}>No trend data available</div>
        )}
      </div>
    </div>
  );
}

/* ---------- Source Distribution (Doughnut Chart) ---------- */
export function SourceDistributionChart({ data = [] }) {
  const chartData = useMemo(
    () => ({
      labels: data.map((d) => d.source),
      datasets: [
        {
          data: data.map((d) => d.count),
          backgroundColor: chartColors.slice(0, data.length),
          borderWidth: 2,
          borderColor: "#fff",
          hoverOffset: 6,
        },
      ],
    }),
    [data],
  );

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          padding: 16,
          usePointStyle: true,
          pointStyle: "circle",
          font: { family: "Inter", size: 11 },
          color: "#4b5563",
        },
      },
      tooltip: {
        backgroundColor: "#111827",
        titleFont: { family: "Inter", size: 12 },
        bodyFont: { family: "Inter", size: 11 },
        padding: 10,
        cornerRadius: 8,
      },
    },
    cutout: "65%",
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Source Distribution</h3>
        <span className={styles.chartBadge}>{data.length} sources</span>
      </div>
      <div className={styles.chartBodySquare}>
        {data.length > 0 ? (
          <Doughnut data={chartData} options={options} />
        ) : (
          <div className={styles.empty}>No source data</div>
        )}
      </div>
    </div>
  );
}

/* ---------- Category Breakdown (Horizontal Bar) ---------- */
export function CategoryChart({ data = [] }) {
  const sorted = useMemo(
    () => [...data].sort((a, b) => b.count - a.count).slice(0, 8),
    [data],
  );

  const chartData = useMemo(
    () => ({
      labels: sorted.map((d) => d.category),
      datasets: [
        {
          data: sorted.map((d) => d.count),
          backgroundColor: chartColors
            .slice(0, sorted.length)
            .map((c) => c + "20"),
          borderColor: chartColors.slice(0, sorted.length),
          borderWidth: 1.5,
          borderRadius: 4,
          barThickness: 24,
        },
      ],
    }),
    [sorted],
  );

  const options = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#111827",
        titleFont: { family: "Inter", size: 12 },
        bodyFont: { family: "Inter", size: 11 },
        padding: 10,
        cornerRadius: 8,
        displayColors: false,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: "#f3f4f6" },
        ticks: { font: { family: "Inter", size: 11 }, color: "#9ca3af" },
      },
      y: {
        grid: { display: false },
        ticks: { font: { family: "Inter", size: 11 }, color: "#4b5563" },
      },
    },
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Subject Breakdown</h3>
        <span className={styles.chartBadge}>{data.length} categories</span>
      </div>
      <div className={styles.chartBodyTall}>
        {sorted.length > 0 ? (
          <Bar data={chartData} options={options} />
        ) : (
          <div className={styles.empty}>No category data</div>
        )}
      </div>
    </div>
  );
}

/* Tools & frameworks visualization removed */
