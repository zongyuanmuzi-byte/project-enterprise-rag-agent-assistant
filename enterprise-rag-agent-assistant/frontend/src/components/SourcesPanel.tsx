import type { SourceItem } from "../api/client";

type SourcesPanelProps = {
  sources?: SourceItem[];
};

export function SourcesPanel({ sources = [] }: SourcesPanelProps) {
  if (sources.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-500">
        没有返回来源。
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sources.map((source, index) => (
        <article key={`${source.filename}-${source.chunk_index}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500">
            <span>{source.filename ?? "未知文件"}</span>
            <span>切片 #{source.chunk_index ?? "无"}</span>
            {typeof source.relevance_score === "number" && <span>相关分 {source.relevance_score.toFixed(3)}</span>}
            {typeof source.distance === "number" && <span>距离 {source.distance.toFixed(3)}</span>}
          </div>
          <p className="mt-2 line-clamp-4 text-sm leading-6 text-slate-700">{source.content}</p>
        </article>
      ))}
    </div>
  );
}
