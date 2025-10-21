import { useState, useEffect, useRef, ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/services/api";
import { Dataset } from "@/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Input,
  Label,
} from "@/components/ui";

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [datasetDescription, setDatasetDescription] = useState("");
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
    }
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

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "ready":
        return "default";
      case "processing":
        return "secondary";
      case "error":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">DataChat Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">
                Welcome back, {user?.username || user?.email}
              </p>
            </div>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Upload Dataset</CardTitle>
            <CardDescription>
              Upload a CSV or XLSX file to start analyzing your data
            </CardDescription>
          </CardHeader>
          <CardContent>
            {uploadError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm mb-4">
                {uploadError}
              </div>
            )}

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="file">File (CSV or XLSX)</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  disabled={isUploading}
                />
                {selectedFile && (
                  <p className="text-sm text-gray-600">
                    Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Dataset Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="My Dataset"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  disabled={isUploading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  type="text"
                  placeholder="Brief description of the dataset"
                  value={datasetDescription}
                  onChange={(e) => setDatasetDescription(e.target.value)}
                  disabled={isUploading}
                />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              className="w-full sm:w-auto"
            >
              {isUploading ? "Uploading..." : "Upload Dataset"}
            </Button>
          </CardFooter>
        </Card>

        {/* Datasets List */}
        <Card>
          <CardHeader>
            <CardTitle>Your Datasets</CardTitle>
            <CardDescription>
              Click on a dataset to start querying with natural language
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm mb-4">
                {error}
              </div>
            )}

            {isLoading ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Loading datasets...</p>
              </div>
            ) : datasets.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">
                  No datasets yet. Upload your first dataset to get started!
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Desktop view - Table */}
                <div className="hidden md:block overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>File</TableHead>
                        <TableHead className="text-right">Size</TableHead>
                        <TableHead className="text-right">Rows</TableHead>
                        <TableHead className="text-right">Columns</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {datasets.map((dataset) => (
                        <TableRow
                          key={dataset.id}
                          className={
                            dataset.status === "ready"
                              ? "cursor-pointer hover:bg-gray-50"
                              : ""
                          }
                          onClick={() =>
                            dataset.status === "ready" &&
                            handleDatasetClick(dataset.id, dataset.status)
                          }
                        >
                          <TableCell className="font-medium">{dataset.name}</TableCell>
                          <TableCell className="max-w-xs truncate">
                            {dataset.description || "-"}
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">
                            {dataset.filename}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatFileSize(dataset.file_size)}
                          </TableCell>
                          <TableCell className="text-right">
                            {dataset.row_count?.toLocaleString() || "-"}
                          </TableCell>
                          <TableCell className="text-right">
                            {dataset.column_count || "-"}
                          </TableCell>
                          <TableCell>
                            <Badge variant={getStatusBadgeVariant(dataset.status)}>
                              {dataset.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteDataset(dataset.id);
                              }}
                            >
                              Delete
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Mobile view - Cards */}
                <div className="md:hidden space-y-4">
                  {datasets.map((dataset) => (
                    <Card
                      key={dataset.id}
                      className={
                        dataset.status === "ready"
                          ? "cursor-pointer hover:shadow-md transition-shadow"
                          : ""
                      }
                      onClick={() => handleDatasetClick(dataset.id, dataset.status)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{dataset.name}</CardTitle>
                            <CardDescription className="mt-1">
                              {dataset.description || "No description"}
                            </CardDescription>
                          </div>
                          <Badge variant={getStatusBadgeVariant(dataset.status)}>
                            {dataset.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <dt className="text-gray-600">File:</dt>
                            <dd className="font-medium">{dataset.filename}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Size:</dt>
                            <dd className="font-medium">
                              {formatFileSize(dataset.file_size)}
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Rows:</dt>
                            <dd className="font-medium">
                              {dataset.row_count?.toLocaleString() || "-"}
                            </dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-600">Columns:</dt>
                            <dd className="font-medium">{dataset.column_count || "-"}</dd>
                          </div>
                        </dl>
                        {dataset.status === "error" && dataset.error_message && (
                          <p className="mt-3 text-sm text-red-600">
                            Error: {dataset.error_message}
                          </p>
                        )}
                      </CardContent>
                      <CardFooter>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteDataset(dataset.id);
                          }}
                          className="w-full"
                        >
                          Delete Dataset
                        </Button>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
