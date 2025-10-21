export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  filename: string;
  file_size: number;
  row_count?: number;
  column_count?: number;
  column_info?: Record<string, any>;
  status: "uploaded" | "processing" | "ready" | "error";
  error_message?: string;
  created_at: string;
  updated_at?: string;
}

export interface Query {
  id: string;
  dataset_id: string;
  natural_language_query: string;
  generated_sql?: string;
  query_type?: string;
  result_data?: Array<Record<string, any>>;
  result_summary?: string;
  execution_time?: number;
  row_count?: number;
  status: "pending" | "success" | "error";
  error_message?: string;
  user_feedback?: "thumbs_up" | "thumbs_down" | "none";
  created_at: string;
  visualization_type?: "bar_chart" | "line_chart" | "pie_chart" | "number" | "table";
}

export interface Insight {
  id: string;
  dataset_id: string;
  query_id?: string;
  insight_type: string;
  title: string;
  description: string;
  confidence_score?: number;
  supporting_data?: any;
  visualization_config?: any;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
