import { Activity, RefreshCw } from "lucide-react";
import { useState } from "react";

import { API_BASE_URL, healthCheck, type HealthResponse } from "../api/client";

function formatStatus(status?: string): string {
  if (!status) {
    return "正常";
  }

  const statusMap: Record<string, string> = {
    ok: "正常",
    healthy: "正常",
    success: "成功",
  };

  return statusMap[status] ?? status;
}

export function HealthCheck() {
  const [status, setStatus] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCheck() {
    setLoading(true);
    setError(null);

    try {
      setStatus(await healthCheck());
    } catch (err) {
      console.error("健康检查失败", {
        apiBaseUrl: API_BASE_URL,
        error: err,
      });
      setError(err instanceof Error ? err.message : `健康检查失败。后端地址：${API_BASE_URL}`);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Activity className="text-slate-700" size={22} aria-hidden="true" />
          <div>
            <h2 className="text-base font-semibold text-slate-950">后端状态</h2>
            <p className="text-sm text-slate-500">检查 FastAPI 服务是否可用。</p>
          </div>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60" onClick={handleCheck} disabled={loading}>
          <RefreshCw size={16} aria-hidden="true" />
          {loading ? "检查中" : "检查"}
        </button>
      </div>

      {(status || error) && (
        <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm">
          {status && (
            <span className="font-medium text-emerald-700">
              {formatStatus(status.status)} - {status.message ?? "后端服务可访问。"}
              <span className="ml-2 text-slate-500">后端地址：{API_BASE_URL}</span>
            </span>
          )}
          {error && <span className="font-medium text-red-700">{error}</span>}
        </div>
      )}
    </section>
  );
}
