export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8010";

export type SourceItem = {
  filename?: string | null;
  chunk_index?: number | null;
  document_id?: number | null;
  content: string;
  distance?: number | null;
  relevance_score?: number | null;
};

export type HealthResponse = {
  status?: string;
  message?: string;
};

export type UploadResponse = {
  document_id: number;
  filename: string;
  chunks_count: number;
  status: string;
};

export type RagResponse = {
  answer: string;
  sources: SourceItem[];
  request_id: string;
  latency_ms: number;
  chat_log_id?: number;
};

export type AgentResponse = {
  intent: string;
  tool_used: string;
  answer: string;
  sources: SourceItem[];
  request_id: string;
  latency_ms: number;
  error?: string | null;
  chat_log_id?: number;
};

export type FeedbackPayload = {
  chat_log_id: number;
  rating: number;
  comment?: string;
};

export type FeedbackResponse = {
  feedback_id: number;
  chat_log_id: number;
  rating: number;
  comment?: string | null;
  status: string;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const headers: HeadersInit = {
    ...init?.headers,
  };

  if (init?.body && !(init.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    response = await fetch(buildUrl(path), {
      ...init,
      headers,
    });
  } catch (error) {
    console.error("API request failed", {
      url: buildUrl(path),
      error,
    });
    throw new Error(`Network Error：无法连接后端服务，请确认 FastAPI 已启动。后端地址：${API_BASE_URL}`);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "请求失败。";
    throw new Error(detail);
  }

  return data as T;
}

function buildUrl(path: string): string {
  if (!API_BASE_URL) {
    return path;
  }

  return `${API_BASE_URL.replace(/\/$/, "")}${path}`;
}

export function healthCheck(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return requestJson<UploadResponse>("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export function askRag(question: string, topK = 3): Promise<RagResponse> {
  return requestJson<RagResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({
      question,
      top_k: topK,
    }),
  });
}

export function askAgent(question: string, topK = 3): Promise<AgentResponse> {
  return requestJson<AgentResponse>("/agent/chat", {
    method: "POST",
    body: JSON.stringify({
      question,
      top_k: topK,
    }),
  });
}

export function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  return requestJson<FeedbackResponse>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
