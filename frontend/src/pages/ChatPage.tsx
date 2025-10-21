import { useState, useEffect, useRef, FormEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/services/api";
import { Dataset, Query, Insight } from "@/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Input,
  ScrollArea,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Badge,
} from "@/components/ui";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  query?: Query;
  timestamp: Date;
}

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
  const [showInsights, setShowInsights] = useState(false);
  const [error, setError] = useState("");

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
        content: err.response?.data?.detail || "Failed to execute query. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(err.response?.data?.detail || "Failed to execute query");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (queryId: string, feedback: "thumbs_up" | "thumbs_down") => {
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
      setShowInsights(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate insights");
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  if (isLoadingDataset) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Loading dataset...</p>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Dataset Not Found</CardTitle>
            <CardDescription>
              The requested dataset could not be found.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate("/dashboard")}>
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={() => navigate("/dashboard")}>
                Back
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{dataset.name}</h1>
                <p className="text-sm text-gray-600">
                  {dataset.row_count?.toLocaleString()} rows, {dataset.column_count} columns
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={dataset.status === "ready" ? "default" : "secondary"}>
                {dataset.status}
              </Badge>
              <Button
                variant="outline"
                onClick={handleGenerateInsights}
                disabled={isGeneratingInsights || dataset.status !== "ready"}
              >
                {isGeneratingInsights ? "Generating..." : "Generate Insights"}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex gap-6">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Chat with your data</CardTitle>
              <CardDescription>
                Ask questions in natural language about your dataset
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0">
              {error && dataset.status !== "ready" && (
                <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md text-sm mb-4">
                  {error}
                </div>
              )}

              {error && dataset.status === "ready" && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm mb-4">
                  {error}
                </div>
              )}

              {/* Messages */}
              <ScrollArea className="flex-1 pr-4 mb-4" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No messages yet. Start by asking a question about your data!</p>
                      <p className="text-sm mt-2">
                        For example: "What are the average sales by region?"
                      </p>
                    </div>
                  )}

                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.type === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-3xl rounded-lg px-4 py-3 ${
                          message.type === "user"
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                        {message.query && message.type === "assistant" && (
                          <div className="mt-3 space-y-3">
                            {/* Query Status */}
                            {message.query.status === "error" && (
                              <div className="bg-red-100 text-red-800 px-3 py-2 rounded text-sm">
                                Error: {message.query.error_message || "Query failed"}
                              </div>
                            )}

                            {/* Query Results */}
                            {message.query.result_data &&
                              message.query.result_data.length > 0 && (
                                <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
                                  <div className="overflow-x-auto max-h-96">
                                    <Table>
                                      <TableHeader>
                                        <TableRow>
                                          {Object.keys(message.query.result_data[0]).map(
                                            (key) => (
                                              <TableHead key={key} className="bg-gray-50">
                                                {key}
                                              </TableHead>
                                            )
                                          )}
                                        </TableRow>
                                      </TableHeader>
                                      <TableBody>
                                        {message.query.result_data.map((row, idx) => (
                                          <TableRow key={idx}>
                                            {Object.values(row).map((value, cellIdx) => (
                                              <TableCell key={cellIdx}>
                                                {value !== null && value !== undefined
                                                  ? String(value)
                                                  : "-"}
                                              </TableCell>
                                            ))}
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </div>
                                </div>
                              )}

                            {/* Query Metadata */}
                            <div className="flex items-center justify-between text-xs text-gray-600 bg-white px-3 py-2 rounded">
                              <div className="flex items-center space-x-4">
                                {message.query.execution_time !== undefined && (
                                  <span>
                                    Execution time: {message.query.execution_time.toFixed(2)}s
                                  </span>
                                )}
                                {message.query.row_count !== undefined && (
                                  <span>
                                    {message.query.row_count} row{message.query.row_count !== 1 ? "s" : ""}
                                  </span>
                                )}
                              </div>

                              {/* Feedback Buttons */}
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() =>
                                    handleFeedback(message.query!.id, "thumbs_up")
                                  }
                                  className={`p-1 rounded hover:bg-gray-100 ${
                                    message.query.user_feedback === "thumbs_up"
                                      ? "text-green-600"
                                      : "text-gray-400"
                                  }`}
                                  title="Helpful"
                                >
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() =>
                                    handleFeedback(message.query!.id, "thumbs_down")
                                  }
                                  className={`p-1 rounded hover:bg-gray-100 ${
                                    message.query.user_feedback === "thumbs_down"
                                      ? "text-red-600"
                                      : "text-gray-400"
                                  }`}
                                  title="Not helpful"
                                >
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input Form */}
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question about your data..."
                  disabled={isLoading || dataset.status !== "ready"}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading || dataset.status !== "ready"}
                >
                  {isLoading ? "Sending..." : "Send"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Insights Panel */}
        {(showInsights || insights.length > 0) && (
          <div className="w-80 flex-shrink-0">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>Insights</CardTitle>
                <CardDescription>
                  AI-generated insights from your data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  {insights.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 text-sm">
                      No insights yet. Click "Generate Insights" to analyze your data.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {insights.map((insight) => (
                        <div
                          key={insight.id}
                          className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-semibold text-sm text-gray-900">
                              {insight.title}
                            </h4>
                            {insight.confidence_score !== undefined && (
                              <Badge variant="outline" className="text-xs">
                                {(insight.confidence_score * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {insight.description}
                          </p>
                          <div className="flex items-center justify-between">
                            <Badge variant="secondary" className="text-xs">
                              {insight.insight_type}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              {new Date(insight.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
