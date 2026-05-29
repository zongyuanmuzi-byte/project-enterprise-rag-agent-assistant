import { Upload } from "lucide-react";
import { useState } from "react";

import { uploadDocument, type UploadResponse } from "../api/client";

function formatUploadStatus(status: string): string {
  const statusMap: Record<string, string> = {
    indexed: "已入库",
    success: "成功",
    uploaded: "已上传",
    completed: "已完成",
  };

  return statusMap[status] ?? status;
}

export function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleUpload() {
    if (!file) {
      setError("请先选择文件。");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      setResult(await uploadDocument(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败。");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-3">
        <Upload className="text-slate-700" size={22} aria-hidden="true" />
        <div>
          <h2 className="text-base font-semibold text-slate-950">上传企业文档</h2>
          <p className="text-sm text-slate-500">支持 .txt、.md 和可提取文本的 .pdf 文件。</p>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700" type="file" accept=".txt,.md,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <button className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60" onClick={handleUpload} disabled={loading}>
          {loading ? "上传中" : "上传"}
        </button>
      </div>

      {error && <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm font-medium text-red-700">{error}</div>}

      {result && (
        <dl className="mt-4 grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-4 text-sm md:grid-cols-4">
          <div>
            <dt className="text-slate-500">文件名</dt>
            <dd className="mt-1 font-medium text-slate-900">{result.filename}</dd>
          </div>
          <div>
            <dt className="text-slate-500">文档 ID</dt>
            <dd className="mt-1 font-medium text-slate-900">{result.document_id}</dd>
          </div>
          <div>
            <dt className="text-slate-500">切片数量</dt>
            <dd className="mt-1 font-medium text-slate-900">{result.chunks_count}</dd>
          </div>
          <div>
            <dt className="text-slate-500">状态</dt>
            <dd className="mt-1 font-medium text-slate-900">{formatUploadStatus(result.status)}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
