import { Search } from "lucide-react";
import { useState } from "react";

import { askRag, type RagResponse } from "../api/client";
import { FeedbackForm } from "./FeedbackForm";
import { ResponseCard } from "./ResponseCard";

export function RagChat() {
  const [question, setQuestion] = useState("公司的退款周期是多久？");
  const [topK, setTopK] = useState(3);
  const [response, setResponse] = useState<RagResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    setLoading(true);
    setError(null);

    try {
      setResponse(await askRag(question, topK));
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG 问答请求失败。");
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-3">
        <Search className="text-slate-700" size={22} aria-hidden="true" />
        <div>
          <h2 className="text-base font-semibold text-slate-950">RAG 问答</h2>
          <p className="text-sm text-slate-500">通过 /chat 直接向知识库提问。</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        <textarea className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-800 outline-none focus:border-slate-500" value={question} onChange={(event) => setQuestion(event.target.value)} />
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            检索数量
            <input className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm" type="number" min={1} value={topK} onChange={(event) => setTopK(Number(event.target.value))} />
          </label>
          <button className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60" onClick={handleAsk} disabled={loading || !question.trim()}>
            {loading ? "提问中" : "向 RAG 提问"}
          </button>
        </div>
      </div>

      {error && <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm font-medium text-red-700">{error}</div>}
      <ResponseCard title="RAG 回答" response={response} />
      <FeedbackForm chatLogId={response?.chat_log_id} />
    </section>
  );
}
