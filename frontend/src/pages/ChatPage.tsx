import { useState, useEffect, useRef, useMemo } from "react";
import type { FormEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Send,
  Sparkles,
  Database,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  PieChart as PieChartIcon,
  BarChart3,
  LineChartIcon,
  Table2,
  Clock,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  Lightbulb,
  Target,
  TrendingDown,
  Activity,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/services/api";
import type { Dataset, Query, Insight } from "@/types";
import { Button, Badge, ScrollArea } from "@/components/ui";
import BarChart from "@/components/charts/BarChart";
import LineChart from "@/components/charts/LineChart";
import PieChart from "@/components/charts/PieChart";

// ============================================================================
// TYPES
// ============================================================================

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  query?: Query;
  timestamp: Date;
  isError?: boolean;
}

type VisualizationType = "bar" | "line" | "pie" | "table" | "number";

interface BarChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
}

interface LineChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
    tension?: number;
  }>;
}

interface PieChartData {
  labels: string[];
  datasets: Array<{
    label?: string;
    data: number[];
    backgroundColor?: string[];
    borderColor?: string[];
    borderWidth?: number;
  }>;
}

type ChartData = BarChartData | LineChartData | PieChartData;

// ============================================================================
// SMART VISUALIZATION DETECTION
// ============================================================================

function detectVisualizationType(
  data: any[],
  query: string,
  sql?: string
): VisualizationType {
  if (!data || data.length === 0) return "table";

  const firstRow = data[0];
  const keys = Object.keys(firstRow);
  const lowerQuery = query.toLowerCase();
  const lowerSql = sql?.toLowerCase() || "";

  // Single value result - show as big number card
  if (data.length === 1 && keys.length === 1) {
    return "number";
  }

  // Check for time series data (dates, months, years)
  const hasTimeColumn = keys.some((key) => {
    const keyLower = key.toLowerCase();
    return (
      keyLower.includes("date") ||
      keyLower.includes("time") ||
      keyLower.includes("month") ||
      keyLower.includes("year") ||
      keyLower.includes("day") ||
      keyLower.includes("period")
    );
  });

  // Time series patterns in query
  const timeSeriesKeywords = [
    "over time",
    "trend",
    "by month",
    "by year",
    "by date",
    "timeline",
    "history",
  ];
  const isTimeSeriesQuery = timeSeriesKeywords.some(
    (keyword) => lowerQuery.includes(keyword) || lowerSql.includes(keyword)
  );

  if (hasTimeColumn || isTimeSeriesQuery) {
    return "line";
  }

  // Check for distribution/percentage queries (pie chart)
  const distributionKeywords = [
    "distribution",
    "percentage",
    "proportion",
    "share",
    "breakdown",
    "composition",
  ];
  const isDistribution = distributionKeywords.some(
    (keyword) => lowerQuery.includes(keyword) || lowerSql.includes(keyword)
  );

  // If data has 2 columns and is small (good for pie chart)
  if (keys.length === 2 && data.length <= 10 && isDistribution) {
    return "pie";
  }

  // Check for aggregation queries (bar chart)
  const aggregationKeywords = [
    "group by",
    "count",
    "sum",
    "avg",
    "average",
    "total",
    "max",
    "min",
    "top",
    "bottom",
    "by category",
    "by region",
    "by type",
  ];
  const hasAggregation = aggregationKeywords.some(
    (keyword) => lowerQuery.includes(keyword) || lowerSql.includes(keyword)
  );

  // Comparison queries (bar chart)
  const comparisonKeywords = [
    "compare",
    "comparison",
    "versus",
    "vs",
    "difference between",
    "ranking",
  ];
  const isComparison = comparisonKeywords.some(
    (keyword) => lowerQuery.includes(keyword)
  );

  // If it looks like aggregated data with reasonable length
  if ((hasAggregation || isComparison) && data.length <= 50) {
    return "bar";
  }

  // Check data structure for numeric columns
  const numericColumns = keys.filter((key) => {
    const value = firstRow[key];
    return typeof value === "number" && !key.toLowerCase().includes("id");
  });

  // If we have categorical + numeric data, use bar chart
  if (numericColumns.length > 0 && keys.length >= 2 && data.length <= 50) {
    return "bar";
  }

  // Small dataset with categories - pie chart
  if (data.length <= 10 && keys.length === 2 && numericColumns.length === 1) {
    return "pie";
  }

  // Default to table for complex data
  return "table";
}

function transformDataForChart(
  data: any[],
  vizType: VisualizationType
): ChartData | null {
  if (!data || data.length === 0 || vizType === "table" || vizType === "number") {
    return null;
  }

  const keys = Object.keys(data[0]);

  // Find label column (first non-numeric or first column)
  const labelColumn =
    keys.find((key) => typeof data[0][key] !== "number") || keys[0];

  // Find numeric columns
  const numericColumns = keys.filter((key) => {
    const value = data[0][key];
    return (
      typeof value === "number" &&
      key !== labelColumn &&
      !key.toLowerCase().includes("id")
    );
  });

  // If no numeric columns found, use the second column
  const valueColumns =
    numericColumns.length > 0 ? numericColumns : [keys[1] || keys[0]];

  const labels = data.map((row) => String(row[labelColumn] || "Unknown"));

  const baseData = valueColumns.map((column) => ({
    label: column.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    data: data.map((row) => {
      const value = row[column];
      return typeof value === "number" ? value : parseFloat(value) || 0;
    }),
  }));

  // Return type-specific data structures
  if (vizType === "pie") {
    return {
      labels,
      datasets: baseData.map((dataset) => ({
        label: dataset.label,
        data: dataset.data,
      })),
    } as PieChartData;
  }

  if (vizType === "line") {
    return {
      labels,
      datasets: baseData.map((dataset) => ({
        label: dataset.label,
        data: dataset.data,
      })),
    } as LineChartData;
  }

  // Default to bar chart
  return {
    labels,
    datasets: baseData.map((dataset) => ({
      label: dataset.label,
      data: dataset.data,
    })),
  } as BarChartData;
}

// ============================================================================
// QUERY VISUALIZATION COMPONENT
// ============================================================================

interface QueryVisualizationProps {
  query: Query;
  userQuery: string;
}

function QueryVisualization({ query, userQuery }: QueryVisualizationProps) {
  const [view, setView] = useState<"chart" | "table">("chart");

  const data = query.result_data || [];
  const vizType = useMemo(
    () => detectVisualizationType(data, userQuery, query.generated_sql),
    [data, userQuery, query.generated_sql]
  );

  const chartData = useMemo(
    () => transformDataForChart(data, vizType),
    [data, vizType]
  );

  if (query.status === "error") {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start space-x-3"
      >
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-red-900">Query Error</p>
          <p className="text-sm text-red-700 mt-1">
            {query.error_message || "Failed to execute query"}
          </p>
        </div>
      </motion.div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-4 text-center">
        <p className="text-sm text-gray-600">No data returned</p>
      </div>
    );
  }

  // Single number display
  if (vizType === "number") {
    const value = data[0][Object.keys(data[0])[0]];
    const formattedValue =
      typeof value === "number"
        ? new Intl.NumberFormat().format(value)
        : String(value);

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-8 text-center"
      >
        <div className="text-5xl font-bold text-white mb-2">
          {formattedValue}
        </div>
        <div className="text-blue-100 text-sm font-medium">
          {Object.keys(data[0])[0]
            .replace(/_/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase())}
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-3">
      {/* View Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          {vizType === "bar" && <BarChart3 className="w-4 h-4" />}
          {vizType === "line" && <LineChartIcon className="w-4 h-4" />}
          {vizType === "pie" && <PieChartIcon className="w-4 h-4" />}
          <span className="font-medium">
            {vizType === "bar" && "Bar Chart"}
            {vizType === "line" && "Line Chart"}
            {vizType === "pie" && "Pie Chart"}
          </span>
        </div>

        <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setView("chart")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              view === "chart"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Chart
          </button>
          <button
            onClick={() => setView("table")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              view === "table"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Table
          </button>
        </div>
      </div>

      {/* Visualization */}
      <AnimatePresence mode="wait">
        {view === "chart" && chartData ? (
          <motion.div
            key="chart"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-white rounded-xl border-2 border-gray-200 p-6"
          >
            {vizType === "bar" && <BarChart data={chartData as BarChartData} />}
            {vizType === "line" && <LineChart data={chartData as LineChartData} />}
            {vizType === "pie" && <PieChart data={chartData as PieChartData} variant="doughnut" />}
          </motion.div>
        ) : (
          <motion.div
            key="table"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden"
          >
            <div className="overflow-x-auto max-h-96">
              <table className="w-full">
                <thead className="bg-gray-50 border-b-2 border-gray-200">
                  <tr>
                    {Object.keys(data[0]).map((key) => (
                      <th
                        key={key}
                        className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                      >
                        {key.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      {Object.values(row).map((value, cellIdx) => (
                        <td
                          key={cellIdx}
                          className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                        >
                          {value !== null && value !== undefined
                            ? typeof value === "number"
                              ? new Intl.NumberFormat().format(value)
                              : String(value)
                            : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Query Metadata */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 rounded-lg text-xs text-gray-600">
        <div className="flex items-center space-x-4">
          {query.execution_time !== undefined && (
            <div className="flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{query.execution_time.toFixed(2)}s</span>
            </div>
          )}
          {query.row_count !== undefined && (
            <div className="flex items-center space-x-1">
              <Table2 className="w-3.5 h-3.5" />
              <span>
                {query.row_count} row{query.row_count !== 1 ? "s" : ""}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// MESSAGE COMPONENT
// ============================================================================

interface MessageBubbleProps {
  message: Message;
  onFeedback: (queryId: string, feedback: "thumbs_up" | "thumbs_down") => void;
}

function MessageBubble({ message, onFeedback }: MessageBubbleProps) {
  if (message.type === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
        className="flex justify-end"
      >
        <div className="max-w-3xl">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-lg">
            <p className="text-sm leading-relaxed">{message.content}</p>
          </div>
          <div className="text-xs text-gray-500 mt-1 text-right">
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex justify-start"
    >
      <div className="max-w-4xl">
        {/* AI Avatar */}
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
            <Sparkles className="w-4 h-4 text-white" />
          </div>

          <div className="flex-1">
            {/* Message Content */}
            <div className="bg-white border-2 border-gray-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
              {message.isError ? (
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700 leading-relaxed">
                    {message.content}
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-gray-800 leading-relaxed mb-4">
                    {message.content}
                  </p>

                  {/* Query Visualization */}
                  {message.query && (
                    <QueryVisualization
                      query={message.query}
                      userQuery={
                        message.query.natural_language_query || message.content
                      }
                    />
                  )}
                </>
              )}
            </div>

            {/* Feedback & Timestamp */}
            <div className="flex items-center justify-between mt-1 px-2">
              <div className="text-xs text-gray-500">
                {message.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>

              {message.query && !message.isError && (
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => onFeedback(message.query!.id, "thumbs_up")}
                    className={`p-1.5 rounded-lg transition-all ${
                      message.query.user_feedback === "thumbs_up"
                        ? "bg-green-100 text-green-600"
                        : "text-gray-400 hover:bg-gray-100 hover:text-green-600"
                    }`}
                    title="Helpful"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onFeedback(message.query!.id, "thumbs_down")}
                    className={`p-1.5 rounded-lg transition-all ${
                      message.query.user_feedback === "thumbs_down"
                        ? "bg-red-100 text-red-600"
                        : "text-gray-400 hover:bg-gray-100 hover:text-red-600"
                    }`}
                    title="Not helpful"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// INSIGHTS SIDEBAR COMPONENT
// ============================================================================

interface InsightsSidebarProps {
  insights: Insight[];
  isGenerating: boolean;
  isOpen: boolean;
  onToggle: () => void;
  onGenerate: () => void;
}

function InsightsSidebar({
  insights,
  isGenerating,
  isOpen,
  onToggle,
  onGenerate,
}: InsightsSidebarProps) {
  const getInsightIcon = (type: string) => {
    const iconClass = "w-4 h-4";
    switch (type.toLowerCase()) {
      case "trend":
        return <TrendingUp className={iconClass} />;
      case "anomaly":
        return <Activity className={iconClass} />;
      case "correlation":
        return <Target className={iconClass} />;
      default:
        return <Lightbulb className={iconClass} />;
    }
  };

  const getInsightColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "trend":
        return "from-blue-500 to-cyan-500";
      case "anomaly":
        return "from-red-500 to-orange-500";
      case "correlation":
        return "from-purple-500 to-pink-500";
      default:
        return "from-green-500 to-emerald-500";
    }
  };

  return (
    <>
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: isOpen ? 384 : 0 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="relative overflow-hidden"
      >
        <div className="w-96 h-full bg-gradient-to-br from-gray-50 to-gray-100 border-l-2 border-gray-200 p-6 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                <Lightbulb className="w-4 h-4 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Insights</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onGenerate}
              disabled={isGenerating}
              className="text-xs"
            >
              {isGenerating ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Sparkles className="w-3 h-3 mr-1" />
                  </motion.div>
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3 mr-1" />
                  Generate
                </>
              )}
            </Button>
          </div>

          {/* Insights List */}
          {insights.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center mx-auto mb-4">
                <Lightbulb className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-sm text-gray-600 mb-4">No insights yet</p>
              <p className="text-xs text-gray-500">
                Click "Generate" to analyze your data and discover insights
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {insights.map((insight, index) => (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="bg-white rounded-xl border-2 border-gray-200 p-4 shadow-sm hover:shadow-md transition-all group"
                >
                  {/* Icon & Badge */}
                  <div className="flex items-start justify-between mb-3">
                    <div
                      className={`w-10 h-10 rounded-lg bg-gradient-to-br ${getInsightColor(
                        insight.insight_type
                      )} flex items-center justify-center text-white shadow-lg`}
                    >
                      {getInsightIcon(insight.insight_type)}
                    </div>
                    {insight.confidence_score !== undefined && (
                      <Badge
                        variant={
                          insight.confidence_score > 0.8
                            ? "default"
                            : insight.confidence_score > 0.6
                            ? "secondary"
                            : "outline"
                        }
                        className="text-xs"
                      >
                        {(insight.confidence_score * 100).toFixed(0)}% confidence
                      </Badge>
                    )}
                  </div>

                  {/* Content */}
                  <h4 className="font-semibold text-sm text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {insight.title}
                  </h4>
                  <p className="text-xs text-gray-600 leading-relaxed mb-3">
                    {insight.description}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <Badge variant="secondary" className="text-xs">
                      {insight.insight_type}
                    </Badge>
                    <span className="text-xs text-gray-400">
                      {new Date(insight.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>

      {/* Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onToggle}
        className="fixed right-4 top-1/2 -translate-y-1/2 z-50 w-10 h-20 bg-gradient-to-br from-purple-600 to-blue-600 text-white rounded-l-xl shadow-lg flex items-center justify-center hover:from-purple-700 hover:to-blue-700 transition-all"
        title={isOpen ? "Hide insights" : "Show insights"}
      >
        {isOpen ? (
          <ChevronRight className="w-5 h-5" />
        ) : (
          <ChevronLeft className="w-5 h-5" />
        )}
      </motion.button>
    </>
  );
}

// ============================================================================
// MAIN CHAT PAGE COMPONENT
// ============================================================================

export default function ChatPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDataset, setIsLoadingDataset] = useState(true);
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [error, setError] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    if (datasetId) {
      loadDataset();
      loadQueries();
      loadInsights();
    }
  }, [datasetId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ============================================================================
  // DATA LOADING
  // ============================================================================

  const loadDataset = async () => {
    if (!datasetId) return;

    setIsLoadingDataset(true);
    setError("");

    try {
      const data = await api.getDataset(datasetId);
      setDataset(data);

      if (data.status !== "ready") {
        setError(`Dataset is ${data.status}. Please wait for it to be ready.`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load dataset");
    } finally {
      setIsLoadingDataset(false);
    }
  };

  const loadQueries = async () => {
    if (!datasetId) return;

    try {
      const queries = await api.getQueries(datasetId);
      const queryMessages: Message[] = queries.flatMap((query) => [
        {
          id: `user-${query.id}`,
          type: "user" as const,
          content: query.natural_language_query,
          timestamp: new Date(query.created_at),
        },
        {
          id: `assistant-${query.id}`,
          type: "assistant" as const,
          content: query.result_summary || "Query executed successfully",
          query,
          timestamp: new Date(query.created_at),
        },
      ]);
      setMessages(queryMessages);
    } catch (err) {
      console.error("Failed to load queries:", err);
    }
  };

  const loadInsights = async () => {
    if (!datasetId) return;

    try {
      const data = await api.getDatasetInsights(datasetId);
      setInsights(data);
    } catch (err) {
      console.error("Failed to load insights:", err);
    }
  };

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || !datasetId || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError("");

    try {
      const query = await api.createQuery(datasetId, userMessage.content);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: "assistant",
        content: query.result_summary || "Query executed successfully",
        query,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: "assistant",
        content:
          err.response?.data?.detail ||
          "Failed to execute query. Please try again.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(err.response?.data?.detail || "Failed to execute query");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleFeedback = async (
    queryId: string,
    feedback: "thumbs_up" | "thumbs_down"
  ) => {
    try {
      await api.updateQueryFeedback(queryId, feedback);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.query?.id === queryId && msg.query
            ? { ...msg, query: { ...msg.query, user_feedback: feedback } }
            : msg
        )
      );
    } catch (err) {
      console.error("Failed to update feedback:", err);
    }
  };

  const handleGenerateInsights = async () => {
    if (!datasetId) return;

    setIsGeneratingInsights(true);
    setError("");

    try {
      const newInsights = await api.generateDatasetInsights(datasetId);
      setInsights(newInsights);
      if (!isSidebarOpen) {
        setIsSidebarOpen(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate insights");
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  // ============================================================================
  // LOADING STATES
  // ============================================================================

  if (isLoadingDataset) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-gray-600 font-medium">Loading dataset...</p>
        </motion.div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center"
        >
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Dataset Not Found
          </h2>
          <p className="text-gray-600 mb-6">
            The requested dataset could not be found.
          </p>
          <Button onClick={() => navigate("/dashboard")} className="w-full">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Return to Dashboard
          </Button>
        </motion.div>
      </div>
    );
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30 flex flex-col">
      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="bg-white/80 backdrop-blur-lg shadow-sm border-b-2 border-gray-200 sticky top-0 z-40"
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Back Button & Dataset Info */}
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate("/dashboard")}
                className="gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div className="h-8 w-px bg-gray-300" />
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                  <Database className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900">
                    {dataset.name}
                  </h1>
                  <p className="text-xs text-gray-600">
                    {dataset.row_count?.toLocaleString()} rows •{" "}
                    {dataset.column_count} columns
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Status & Insights Button */}
            <div className="flex items-center space-x-3">
              <Badge
                variant={dataset.status === "ready" ? "default" : "secondary"}
                className="text-xs px-3 py-1"
              >
                {dataset.status}
              </Badge>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full p-6">
          {/* Error Banner */}
          <AnimatePresence>
            {error && dataset.status === "ready" && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mb-4 bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center space-x-2"
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-6 mb-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-16"
              >
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-6 shadow-xl">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Start a conversation
                </h2>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Ask questions about your data in natural language and get instant
                  insights with beautiful visualizations
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {[
                    "What are the top 10 values by amount?",
                    "Show me the trend over time",
                    "What is the average by category?",
                    "Find any unusual patterns",
                  ].map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(example)}
                      className="px-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 transition-all text-left"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onFeedback={handleFeedback}
              />
            ))}

            {isLoading && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex justify-start"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-md">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white border-2 border-gray-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                        className="w-2 h-2 bg-blue-600 rounded-full"
                      />
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: 0.2,
                        }}
                        className="w-2 h-2 bg-purple-600 rounded-full"
                      />
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: 0.4,
                        }}
                        className="w-2 h-2 bg-blue-600 rounded-full"
                      />
                      <span className="text-sm text-gray-600 ml-2">
                        Analyzing your question...
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <motion.form
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            onSubmit={handleSubmit}
            className="bg-white rounded-2xl shadow-xl border-2 border-gray-200 p-4 flex items-end space-x-3"
          >
            <div className="flex-1">
              <input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask anything about your data..."
                disabled={isLoading || dataset.status !== "ready"}
                className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-all text-sm"
              />
            </div>
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading || dataset.status !== "ready"}
              className="bg-gradient-to-br from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl px-6 py-3 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-5 h-5" />
                </motion.div>
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </motion.form>
        </div>

        {/* Insights Sidebar */}
        <InsightsSidebar
          insights={insights}
          isGenerating={isGeneratingInsights}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onGenerate={handleGenerateInsights}
        />
      </div>
    </div>
  );
}
