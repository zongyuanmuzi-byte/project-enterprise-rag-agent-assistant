import { Send } from "lucide-react";
import { useState } from "react";

import { submitFeedback } from "../api/client";

type FeedbackFormProps = {
  chatLogId?: number;
};

export function FeedbackForm({ chatLogId }: FeedbackFormProps) {
  const [rating, setRating] = useState(4);
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!chatLogId) {
      return;
    }

    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const result = await submitFeedback({
        chat_log_id: chatLogId,
        rating,
        comment: comment.trim() || undefined,
      });
      setStatus(`反馈已提交：#${result.feedback_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "反馈提交失败。");
    } finally {
      setLoading(false);
    }
  }

  if (!chatLogId) {
    return (
      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        反馈功能需要后端响应中包含 chat_log_id。
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-950">反馈</h3>
      <div className="mt-3 grid gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          评分
          <input className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm" type="number" min={1} max={5} value={rating} onChange={(event) => setRating(Number(event.target.value))} />
        </label>
        <textarea className="min-h-20 rounded-lg border border-slate-300 px-3 py-2 text-sm leading-6 outline-none focus:border-slate-500" placeholder="可选反馈备注" value={comment} onChange={(event) => setComment(event.target.value)} />
        <button className="inline-flex w-fit items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60" onClick={handleSubmit} disabled={loading}>
          <Send size={16} aria-hidden="true" />
          {loading ? "提交中" : "提交反馈"}
        </button>
      </div>
      {status && <div className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm font-medium text-emerald-700">{status}</div>}
      {error && <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm font-medium text-red-700">{error}</div>}
    </div>
  );
}
