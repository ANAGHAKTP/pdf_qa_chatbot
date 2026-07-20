export type DocStatus = 'uploading' | 'extracting' | 'chunking' | 'embedding' | 'indexing' | 'ready' | 'failed';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  is_active: boolean;
  role: string;
  created_at: string;
}

export interface Folder {
  id: number;
  name: string;
  parent_id: number | null;
  user_id: number;
  created_at: string;
}

export interface Document {
  id: number;
  filename: string;
  filepath: string;
  file_size: number;
  chunk_count: number;
  page_count?: number;
  language?: string;
  status: DocStatus;
  s3_key: string | null;
  folder_id: number | null;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface Citation {
  citation_num: number;
  doc_id: number;
  filename: string;
  page: number;
  chunk_idx: number;
  chunk_id?: string;
  score: number;
  highlighted_paragraph: string;
  preview_url?: string;
}

export interface ConfidenceReport {
  level: 'HIGH' | 'MEDIUM' | 'LOW';
  score: number;
  retrieval_score: number;
  reranker_score: number;
  citation_coverage: number;
  context_consistency: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  created_at: string;
  confidence_level?: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_score?: number;
  metrics?: {
    embedding_time_ms: number;
    retrieval_time_ms: number;
    llm_time_ms: number;
    total_time_ms: number;
    token_count: number;
    confidence_level?: 'HIGH' | 'MEDIUM' | 'LOW';
    confidence_score?: number;
  } | null;
}

export interface ChatSession {
  id: string;
  title: string;
  user_id: number;
  is_pinned?: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentAnalysis {
  summary: string;
  key_insights: string[];
  action_items: string[];
  risks: string[];
  keywords: string[];
  entities: {
    organizations: string[];
    people: string[];
    dates: string[];
    monetary_values: string[];
  };
  timeline: string[];
  tables_summary: string;
}
