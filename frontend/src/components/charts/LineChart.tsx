import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { ChartOptions } from "chart.js";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import ChartContainer from "./ChartContainer";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface LineChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      borderColor?: string;
      backgroundColor?: string;
      fill?: boolean;
      tension?: number;
    }>;
  };
  title?: string;
  description?: string;
  isLoading?: boolean;
  error?: string;
  options?: ChartOptions<"line">;
  smooth?: boolean;
  fill?: boolean;
}

export default function LineChart({
  data,
  title,
  description,
  isLoading = false,
  error,
  options,
  smooth = true,
  fill = true,
}: LineChartProps) {
  const chartRef = useRef<ChartJS<"line">>(null);

  // Default gradient colors
  const defaultBorderColors = [
    "rgba(59, 130, 246, 1)", // blue
    "rgba(168, 85, 247, 1)", // purple
    "rgba(236, 72, 153, 1)", // pink
    "rgba(16, 185, 129, 1)", // green
    "rgba(245, 158, 11, 1)", // orange
  ];

  const defaultBackgroundColors = [
    "rgba(59, 130, 246, 0.1)",
    "rgba(168, 85, 247, 0.1)",
    "rgba(236, 72, 153, 0.1)",
    "rgba(16, 185, 129, 0.1)",
    "rgba(245, 158, 11, 0.1)",
  ];

  // Enhance data with default colors and styles
  const enhancedData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => ({
      ...dataset,
      borderColor: dataset.borderColor || defaultBorderColors[index % defaultBorderColors.length],
      backgroundColor: dataset.backgroundColor || defaultBackgroundColors[index % defaultBackgroundColors.length],
      borderWidth: 3,
      fill: dataset.fill !== undefined ? dataset.fill : fill,
      tension: dataset.tension !== undefined ? dataset.tension : (smooth ? 0.4 : 0),
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: dataset.borderColor || defaultBorderColors[index % defaultBorderColors.length],
      pointBorderColor: "#fff",
      pointBorderWidth: 2,
      pointHoverBackgroundColor: "#fff",
      pointHoverBorderColor: dataset.borderColor || defaultBorderColors[index % defaultBorderColors.length],
      pointHoverBorderWidth: 3,
    })),
  };

  const defaultOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 2,
    interaction: {
      mode: "index" as const,
      intersect: false,
    },
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
        <Line ref={chartRef} data={enhancedData} options={mergedOptions} />
      </motion.div>
    </ChartContainer>
  );
}
