import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { ChartOptions } from "chart.js";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import ChartContainer from "./ChartContainer";

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface BarChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string | string[];
      borderWidth?: number;
    }>;
  };
  title?: string;
  description?: string;
  isLoading?: boolean;
  error?: string;
  options?: ChartOptions<"bar">;
  horizontal?: boolean;
  stacked?: boolean;
}

export default function BarChart({
  data,
  title,
  description,
  isLoading = false,
  error,
  options,
  horizontal = false,
  stacked = false,
}: BarChartProps) {
  const chartRef = useRef<ChartJS<"bar">>(null);

  // Default gradient colors
  const defaultColors = [
    "rgba(59, 130, 246, 0.8)", // blue
    "rgba(168, 85, 247, 0.8)", // purple
    "rgba(236, 72, 153, 0.8)", // pink
    "rgba(16, 185, 129, 0.8)", // green
    "rgba(245, 158, 11, 0.8)", // orange
  ];

  const defaultBorderColors = [
    "rgba(59, 130, 246, 1)",
    "rgba(168, 85, 247, 1)",
    "rgba(236, 72, 153, 1)",
    "rgba(16, 185, 129, 1)",
    "rgba(245, 158, 11, 1)",
  ];

  // Enhance data with default colors if not provided
  const enhancedData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || defaultColors[index % defaultColors.length],
      borderColor: dataset.borderColor || defaultBorderColors[index % defaultBorderColors.length],
      borderWidth: dataset.borderWidth || 2,
      borderRadius: 8,
      borderSkipped: false,
    })),
  };

  const defaultOptions: ChartOptions<"bar"> = {
    indexAxis: horizontal ? "y" : "x",
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 2,
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: 600,
          },
        },
      },
      title: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        padding: 12,
        cornerRadius: 8,
        titleFont: {
          size: 14,
          weight: "bold",
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          label: function (context) {
            let label = context.dataset.label || "";
            if (label) {
              label += ": ";
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat().format(context.parsed.y);
            }
            return label;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: stacked,
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
            weight: 500,
          },
        },
      },
      y: {
        stacked: stacked,
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
        ticks: {
          font: {
            size: 11,
            weight: 500,
          },
          callback: function (value) {
            return new Intl.NumberFormat().format(value as number);
          },
        },
      },
    },
    animation: {
      duration: 1000,
      easing: "easeInOutQuart",
    },
  };

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    plugins: {
      ...defaultOptions.plugins,
      ...options?.plugins,
    },
    scales: {
      ...defaultOptions.scales,
      ...options?.scales,
    },
  };

  useEffect(() => {
    // Trigger animation on mount
    if (chartRef.current) {
      chartRef.current.update();
    }
  }, [data]);

  return (
    <ChartContainer
      title={title}
      description={description}
      isLoading={isLoading}
      error={error}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Bar ref={chartRef} data={enhancedData} options={mergedOptions} />
      </motion.div>
    </ChartContainer>
  );
}
