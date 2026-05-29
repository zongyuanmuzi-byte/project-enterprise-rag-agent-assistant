import type { AgentResponse, RagResponse } from "../api/client";
import { SourcesPanel } from "./SourcesPanel";

type ResponseCardProps = {
  title: string;
  response?: RagResponse | AgentResponse | null;
};

function isAgentResponse(response: RagResponse | AgentResponse): response is AgentResponse {
  return "intent" in response;
}

function formatIntent(intent: string): string {
  const intentMap: Record<string, string> = {
    document_qa: "知识库问答",
    summary: "总结",
    writing: "写作",
    general_chat: "通用聊天",
  };

  return intentMap[intent] ?? intent;
}

function formatTool(tool: string): string {
  const toolMap: Record<string, string> = {
    rag_tool: "知识库工具",
    summary_tool: "总结工具",
    writing_tool: "写作工具",
    general_chat_tool: "通用聊天工具",
  };

  return toolMap[tool] ?? tool;
}

export function ResponseCard({ title, response }: ResponseCardProps) {
  if (!response) {
    return null;
  }

  return (
    <section className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
          <span>{response.latency_ms} 毫秒</span>
          <span>请求 ID {response.request_id}</span>
        </div>
      </div>

      {isAgentResponse(response) && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-md bg-blue-50 px-2 py-1 font-medium text-blue-700">意图：{formatIntent(response.intent)}</span>
          <span className="rounded-md bg-emerald-50 px-2 py-1 font-medium text-emerald-700">工具：{formatTool(response.tool_used)}</span>
          {response.error && <span className="rounded-md bg-red-50 px-2 py-1 font-medium text-red-700">错误：{response.error}</span>}
        </div>
      )}

      <div className="mt-4 rounded-lg bg-white p-4 text-sm leading-7 text-slate-800 whitespace-pre-wrap">{response.answer}</div>

      <div className="mt-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">来源</h4>
        <SourcesPanel sources={response.sources} />
      </div>
    </section>
  );
}
