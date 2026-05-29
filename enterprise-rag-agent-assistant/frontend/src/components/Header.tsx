import { DatabaseZap } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-6">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-900 text-white">
          <DatabaseZap size={24} aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">企业 RAG Agent 助手</h1>
          <p className="mt-1 text-sm text-slate-600">企业知识库 RAG + Agent 演示界面</p>
        </div>
      </div>
    </header>
  );
}
