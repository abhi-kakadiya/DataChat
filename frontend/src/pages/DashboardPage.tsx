import { useState, useEffect, useRef } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/services/api";
import type { Dataset } from "@/types";
import { Button } from "@/components/ui";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  Database,
  Activity,
  TrendingUp,
  LogOut,
  Trash2,
  Check,
  Clock,
  AlertCircle,
  Sparkles,
  BarChart3,
  FileSpreadsheet,
  CheckCircle2,
  Loader2,
  X,
  Search,
} from "lucide-react";

// Skeleton loader component
const SkeletonCard = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-white rounded-2xl p-6 border border-gray-100"
  >
    <div className="animate-pulse space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-6 bg-gray-200 rounded w-1/2"></div>
        <div className="h-6 bg-gray-200 rounded-full w-20"></div>
      </div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-200 rounded"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
      </div>
    </div>
  </motion.div>
);

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [datasetDescription, setDatasetDescription] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const navigate = useNavigate();
  const { user, logout } = useAuth();

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await api.getDatasets();
      setDatasets(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load datasets");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    const fileExtension = file.name.split(".").pop()?.toLowerCase();
    if (fileExtension !== "csv" && fileExtension !== "xlsx") {
      setUploadError("Please select a CSV or XLSX file");
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setUploadError("");
    if (!datasetName) {
      setDatasetName(file.name.replace(/\.(csv|xlsx)$/i, ""));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError("Please select a file");
      return;
    }

    if (!datasetName.trim()) {
      setUploadError("Please provide a dataset name");
      return;
    }

    setIsUploading(true);
    setUploadError("");

    try {
      await api.uploadDataset(selectedFile, datasetName, datasetDescription);
      setSelectedFile(null);
      setDatasetName("");
      setDatasetDescription("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadDatasets();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || "Failed to upload dataset");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this dataset?")) {
      return;
    }

    try {
      await api.deleteDataset(id);
      await loadDatasets();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete dataset");
    }
  };

  const handleDatasetClick = (datasetId: string, status: string) => {
    if (status === "ready") {
      navigate(`/chat/${datasetId}`);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case "ready":
        return {
          icon: CheckCircle2,
          color: "text-green-600",
          bgColor: "bg-green-50",
          borderColor: "border-green-200",
          label: "Ready",
        };
      case "processing":
        return {
          icon: Loader2,
          color: "text-blue-600",
          bgColor: "bg-blue-50",
          borderColor: "border-blue-200",
          label: "Processing",
        };
      case "error":
        return {
          icon: AlertCircle,
          color: "text-red-600",
          bgColor: "bg-red-50",
          borderColor: "border-red-200",
          label: "Error",
        };
      default:
        return {
          icon: Clock,
          color: "text-gray-600",
          bgColor: "bg-gray-50",
          borderColor: "border-gray-200",
          label: status,
        };
    }
  };

  const stats = [
    {
      label: "Total Datasets",
      value: datasets.length,
      icon: Database,
      color: "from-blue-500 to-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      label: "Ready to Analyze",
      value: datasets.filter((d) => d.status === "ready").length,
      icon: CheckCircle2,
      color: "from-green-500 to-green-600",
      bgColor: "bg-green-50",
    },
    {
      label: "Processing",
      value: datasets.filter((d) => d.status === "processing").length,
      icon: Activity,
      color: "from-purple-500 to-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      label: "Total Rows",
      value: datasets
        .reduce((acc, d) => acc + (d.row_count || 0), 0)
        .toLocaleString(),
      icon: TrendingUp,
      color: "from-pink-500 to-pink-600",
      bgColor: "bg-pink-50",
    },
  ];

  const filteredDatasets = datasets.filter((dataset) =>
    dataset.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      {/* Header */}
      <motion.header
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative bg-white border-b border-gray-200 overflow-hidden"
      >
        {/* Animated background pattern */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5"></div>
        <motion.div
          animate={{
            backgroundPosition: ["0% 0%", "100% 100%"],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            repeatType: "reverse",
          }}
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.1) 0%, transparent 50%)",
            backgroundSize: "200% 200%",
          }}
        />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="flex items-center space-x-3"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                    DataChat Dashboard
                  </h1>
                  <p className="text-sm text-gray-600 mt-1">
                    Welcome back, <span className="font-semibold">{user?.username || user?.email}</span>
                  </p>
                </div>
              </motion.div>
            </div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Button
                variant="outline"
                onClick={logout}
                className="group hover:border-red-300 hover:bg-red-50 transition-all"
              >
                <LogOut className="w-4 h-4 mr-2 group-hover:text-red-600 transition-colors" />
                <span className="group-hover:text-red-600 transition-colors">Logout</span>
              </Button>
            </motion.div>
          </div>
        </div>
      </motion.header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
              whileHover={{ y: -5, transition: { duration: 0.2 } }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative bg-white rounded-2xl p-6 border border-gray-100 shadow-sm group-hover:shadow-lg transition-all duration-300">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 ${stat.bgColor} rounded-xl flex items-center justify-center`}>
                    <stat.icon className={`w-6 h-6 bg-gradient-to-br ${stat.color} bg-clip-text text-transparent`} style={{ WebkitTextFillColor: 'transparent' }} />
                  </div>
                  <motion.div
                    animate={{
                      scale: [1, 1.2, 1],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      repeatDelay: 3,
                    }}
                    className={`w-2 h-2 rounded-full bg-gradient-to-br ${stat.color}`}
                  ></motion.div>
                </div>
                <h3 className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</h3>
                <p className="text-sm text-gray-600 font-medium">{stat.label}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="relative group"
        >
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl opacity-0 group-hover:opacity-100 blur transition-opacity duration-300"></div>
          <div className="relative bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Upload className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Upload Dataset</h2>
                  <p className="text-sm text-gray-600">Upload a CSV or XLSX file to start analyzing</p>
                </div>
              </div>

              {uploadError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start space-x-3"
                >
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700 font-medium">{uploadError}</p>
                </motion.div>
              )}

              {/* Drag and Drop Area */}
              <motion.div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                whileHover={{ scale: 1.01 }}
                className={`relative border-2 border-dashed rounded-2xl p-8 mb-6 transition-all duration-300 ${
                  isDragging
                    ? "border-blue-500 bg-blue-50"
                    : selectedFile
                    ? "border-green-500 bg-green-50"
                    : "border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/50"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={isUploading}
                />

                <div className="text-center">
                  {selectedFile ? (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="flex items-center justify-center space-x-4"
                    >
                      <div className="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center">
                        <FileSpreadsheet className="w-8 h-8 text-green-600" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-semibold text-gray-900">{selectedFile.name}</p>
                        <p className="text-sm text-gray-600">{formatFileSize(selectedFile.size)}</p>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedFile(null);
                          if (fileInputRef.current) fileInputRef.current.value = "";
                        }}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        <X className="w-5 h-5 text-red-600" />
                      </button>
                    </motion.div>
                  ) : (
                    <>
                      <motion.div
                        animate={{
                          y: [0, -10, 0],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }}
                        className="w-16 h-16 mx-auto bg-blue-100 rounded-xl flex items-center justify-center mb-4"
                      >
                        <Upload className="w-8 h-8 text-blue-600" />
                      </motion.div>
                      <p className="text-gray-900 font-semibold mb-2">
                        {isDragging ? "Drop your file here" : "Drag and drop your file here"}
                      </p>
                      <p className="text-sm text-gray-600 mb-4">or</p>
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        Browse Files
                      </Button>
                      <p className="text-xs text-gray-500 mt-4">Supports CSV and XLSX files</p>
                    </>
                  )}
                </div>
              </motion.div>

              {/* Form Fields */}
              {selectedFile && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Dataset Name *
                    </label>
                    <input
                      type="text"
                      placeholder="My Dataset"
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                      disabled={isUploading}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description (optional)
                    </label>
                    <input
                      type="text"
                      placeholder="Brief description of the dataset"
                      value={datasetDescription}
                      onChange={(e) => setDatasetDescription(e.target.value)}
                      disabled={isUploading}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    />
                  </div>

                  <Button
                    onClick={handleUpload}
                    disabled={!selectedFile || isUploading}
                    className="w-full h-12 bg-gradient-to-r from-blue-500 via-purple-600 to-pink-600 hover:from-blue-600 hover:via-purple-700 hover:to-pink-700 text-white font-semibold shadow-lg"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-5 w-5" />
                        Upload Dataset
                      </>
                    )}
                  </Button>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Datasets Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Your Datasets</h2>
                <p className="text-sm text-gray-600">Click on a dataset to start querying</p>
              </div>
            </div>

            {/* Search Bar */}
            {datasets.length > 0 && (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search datasets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                />
              </div>
            )}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start space-x-3"
            >
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </motion.div>
          )}

          {/* Loading State */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : filteredDatasets.length === 0 ? (
            /* Empty State */
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="text-center py-16 bg-white rounded-2xl border border-gray-100"
            >
              <motion.div
                animate={{
                  y: [0, -10, 0],
                  rotate: [0, 5, -5, 0],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center"
              >
                <Database className="w-12 h-12 text-gray-400" />
              </motion.div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {searchQuery ? "No datasets found" : "No datasets yet"}
              </h3>
              <p className="text-gray-600 mb-6">
                {searchQuery
                  ? "Try adjusting your search query"
                  : "Upload your first dataset to get started with AI-powered analytics!"}
              </p>
              {!searchQuery && (
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Dataset
                </Button>
              )}
            </motion.div>
          ) : (
            /* Dataset Cards Grid */
            <motion.div
              layout
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              <AnimatePresence>
                {filteredDatasets.map((dataset, index) => {
                  const statusConfig = getStatusConfig(dataset.status);
                  const StatusIcon = statusConfig.icon;
                  const isReady = dataset.status === "ready";

                  return (
                    <motion.div
                      key={dataset.id}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      whileHover={{ y: -8, transition: { duration: 0.2 } }}
                      onClick={() => handleDatasetClick(dataset.id, dataset.status)}
                      className={`relative group ${
                        isReady ? "cursor-pointer" : ""
                      }`}
                    >
                      {/* Card Glow Effect */}
                      <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl opacity-0 group-hover:opacity-100 blur transition-opacity duration-300"></div>

                      {/* Card */}
                      <div className="relative bg-white rounded-2xl border border-gray-100 shadow-sm group-hover:shadow-xl transition-all duration-300 overflow-hidden">
                        {/* Status Badge */}
                        <div className="absolute top-4 right-4 z-10">
                          <div
                            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full ${statusConfig.bgColor} border ${statusConfig.borderColor}`}
                          >
                            <StatusIcon
                              className={`w-4 h-4 ${statusConfig.color} ${
                                dataset.status === "processing" ? "animate-spin" : ""
                              }`}
                            />
                            <span className={`text-xs font-semibold ${statusConfig.color}`}>
                              {statusConfig.label}
                            </span>
                          </div>
                        </div>

                        <div className="p-6">
                          {/* Icon */}
                          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                            <BarChart3 className="w-6 h-6 text-white" />
                          </div>

                          {/* Title */}
                          <h3 className="text-lg font-bold text-gray-900 mb-2 pr-24 line-clamp-1">
                            {dataset.name}
                          </h3>

                          {/* Description */}
                          <p className="text-sm text-gray-600 mb-4 line-clamp-2 min-h-[2.5rem]">
                            {dataset.description || "No description provided"}
                          </p>

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 gap-3 mb-4 pb-4 border-b border-gray-100">
                            <div className="bg-gray-50 rounded-lg p-3">
                              <p className="text-xs text-gray-600 mb-1">Rows</p>
                              <p className="text-lg font-bold text-gray-900">
                                {dataset.row_count?.toLocaleString() || "-"}
                              </p>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-3">
                              <p className="text-xs text-gray-600 mb-1">Columns</p>
                              <p className="text-lg font-bold text-gray-900">
                                {dataset.column_count || "-"}
                              </p>
                            </div>
                          </div>

                          {/* File Info */}
                          <div className="flex items-center justify-between text-xs text-gray-600 mb-4">
                            <span className="flex items-center">
                              <FileSpreadsheet className="w-3 h-3 mr-1" />
                              {dataset.filename}
                            </span>
                            <span>{formatFileSize(dataset.file_size)}</span>
                          </div>

                          {/* Error Message */}
                          {dataset.status === "error" && dataset.error_message && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                              <p className="text-xs text-red-700">{dataset.error_message}</p>
                            </div>
                          )}

                          {/* Actions */}
                          <div className="flex space-x-2">
                            {isReady && (
                              <Button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDatasetClick(dataset.id, dataset.status);
                                }}
                                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
                              >
                                <Sparkles className="w-4 h-4 mr-2" />
                                Analyze
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteDataset(dataset.id);
                              }}
                              className={`${isReady ? "" : "flex-1"} border-red-200 hover:bg-red-50 hover:border-red-300 group/delete`}
                            >
                              <Trash2 className="w-4 h-4 text-red-600 group-hover/delete:scale-110 transition-transform" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
