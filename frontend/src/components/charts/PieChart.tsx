import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { ChartOptions } from "chart.js";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Pie, Doughnut } from "react-chartjs-2";
import ChartContainer from "./ChartContainer";

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      label?: string;
      data: number[];
      backgroundColor?: string[];
      borderColor?: string[];
      borderWidth?: number;
    }>;
  };
  title?: string;
  description?: string;
  isLoading?: boolean;
  error?: string;
  options?: ChartOptions<"pie"> | ChartOptions<"doughnut">;
  variant?: "pie" | "doughnut";
}

export default function PieChart({
  data,
  title,
  description,
  isLoading = false,
  error,
  options,
  variant = "doughnut",
}: PieChartProps) {
  const chartRef = useRef<ChartJS<"pie"> | ChartJS<"doughnut">>(null);

  // Beautiful gradient color palette
  const defaultBackgroundColors = [
    "rgba(59, 130, 246, 0.8)", // blue
    "rgba(168, 85, 247, 0.8)", // purple
    "rgba(236, 72, 153, 0.8)", // pink
    "rgba(16, 185, 129, 0.8)", // green
    "rgba(245, 158, 11, 0.8)", // orange
    "rgba(239, 68, 68, 0.8)", // red
    "rgba(20, 184, 166, 0.8)", // teal
    "rgba(99, 102, 241, 0.8)", // indigo
    "rgba(217, 70, 239, 0.8)", // fuchsia
    "rgba(34, 197, 94, 0.8)", // emerald
  ];

  const defaultBorderColors = [
    "rgba(59, 130, 246, 1)",
    "rgba(168, 85, 247, 1)",
    "rgba(236, 72, 153, 1)",
    "rgba(16, 185, 129, 1)",
    "rgba(245, 158, 11, 1)",
    "rgba(239, 68, 68, 1)",
    "rgba(20, 184, 166, 1)",
    "rgba(99, 102, 241, 1)",
    "rgba(217, 70, 239, 1)",
    "rgba(34, 197, 94, 1)",
  ];

  // Enhance data with default colors
  const enhancedData = {
    ...data,
    datasets: data.datasets.map((dataset) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || defaultBackgroundColors,
      borderColor: dataset.borderColor || defaultBorderColors,
      borderWidth: dataset.borderWidth || 2,
      hoverOffset: 8,
    })),
  };

  const defaultOptions: ChartOptions<"pie"> | ChartOptions<"doughnut"> = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 1.5,
    plugins: {
      legend: {
        position: "right" as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
            weight: 600,
          },
          generateLabels: (chart: any) => {
            const data = chart.data;
            if (data.labels && data.datasets.length) {
              return data.labels.map((label: any, i: number) => {
                const value = data.datasets[0].data[i] as number;
                const total = (data.datasets[0].data as number[]).reduce((a: number, b: number) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return {
                  text: `${label} (${percentage}%)`,
                  fillStyle: (data.datasets[0].backgroundColor as string[])?.[i] || defaultBackgroundColors[i],
                  hidden: false,
                  index: i,
                };
              });
            }
            return [];
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
          label: function (context: any) {
            const label = context.label || "";
            const value = context.parsed;
            const total = (context.dataset.data as number[]).reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${new Intl.NumberFormat().format(value)} (${percentage}%)`;
          },
        },
      },
    },
    animation: {
      animateRotate: true,
      animateScale: true,
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
  };

  useEffect(() => {
    // Trigger animation on mount
    if (chartRef.current) {
      chartRef.current.update();
    }
  }, [data]);

  const ChartComponent = variant === "pie" ? Pie : Doughnut;

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
        className="flex items-center justify-center"
      >
        <ChartComponent
          ref={chartRef as any}
          data={enhancedData}
          options={mergedOptions as any}
        />
      </motion.div>
    </ChartContainer>
  );
}
