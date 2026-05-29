import { AgentChat } from "./components/AgentChat";
import { DocumentUpload } from "./components/DocumentUpload";
import { Header } from "./components/Header";
import { HealthCheck } from "./components/HealthCheck";
import { RagChat } from "./components/RagChat";

function App() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <Header />
      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-6">
        <HealthCheck />
        <DocumentUpload />
        <div className="grid gap-6 xl:grid-cols-2">
          <RagChat />
          <AgentChat />
        </div>
      </main>
    </div>
  );
}

export default App;
