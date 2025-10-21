import axios, { AxiosInstance } from "axios";
import type { User, Dataset, Query, Insight, LoginRequest, RegisterRequest, AuthResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Auth
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post("/auth/login", data);
    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post("/auth/register", data);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get("/users/me");
    return response.data;
  }

  // Datasets
  async uploadDataset(file: File, name: string, description: string): Promise<Dataset> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("description", description);

    const response = await this.client.post("/datasets/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  }

  async getDatasets(): Promise<Dataset[]> {
    const response = await this.client.get("/datasets/");
    return response.data;
  }

  async getDataset(id: string): Promise<Dataset> {
    const response = await this.client.get(`/datasets/${id}`);
    return response.data;
  }

  async getDatasetPreview(id: string, limit = 10): Promise<any> {
    const response = await this.client.get(`/datasets/${id}/preview?limit=${limit}`);
    return response.data;
  }

  async deleteDataset(id: string): Promise<void> {
    await this.client.delete(`/datasets/${id}`);
  }

  // Queries
  async createQuery(datasetId: string, query: string): Promise<Query> {
    const response = await this.client.post("/queries/", {
      dataset_id: datasetId,
      natural_language_query: query,
    });
    return response.data;
  }

  async getQueries(datasetId?: string): Promise<Query[]> {
    const url = datasetId ? `/queries/dataset/${datasetId}` : "/queries/";
    const response = await this.client.get(url);
    return response.data.queries || response.data;
  }

  async getQuery(id: string): Promise<Query> {
    const response = await this.client.get(`/queries/${id}`);
    return response.data;
  }

  async updateQueryFeedback(id: string, feedback: string): Promise<Query> {
    const response = await this.client.patch(`/queries/${id}`, {
      user_feedback: feedback,
    });
    return response.data;
  }

  // Insights
  async generateDatasetInsights(datasetId: string, maxInsights = 5): Promise<Insight[]> {
    const response = await this.client.post(
      `/insights/generate/dataset/${datasetId}?max_insights=${maxInsights}`
    );
    return response.data;
  }

  async generateQueryInsights(queryId: string, maxInsights = 3): Promise<Insight[]> {
    const response = await this.client.post(
      `/insights/generate/query/${queryId}?max_insights=${maxInsights}`
    );
    return response.data;
  }

  async getDatasetInsights(datasetId: string): Promise<Insight[]> {
    const response = await this.client.get(`/insights/dataset/${datasetId}`);
    return response.data.insights || response.data;
  }
}

export const api = new ApiClient();
