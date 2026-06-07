import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/50 text-blue-400 text-sm border border-blue-800">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          Pipeline Active
        </div>

        <h1 className="text-5xl font-bold tracking-tight">
          <span className="text-blue-400">ClaimPilot</span>
        </h1>
        <p className="text-xl text-gray-400">
          Autonomous Insurance Claims Processing Agent
        </p>
        <p className="text-gray-500 italic">
          &ldquo;From inbox to settlement — without a human reading it.&rdquo;
        </p>

        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            Adjuster Dashboard
          </Link>
          <Link
            href="/api/v1"
            className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-colors border border-gray-700"
          >
            API Docs
          </Link>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-8 text-center">
          <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
            <div className="text-2xl font-bold text-green-400">6</div>
            <div className="text-sm text-gray-400">Specialized Agents</div>
          </div>
          <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
            <div className="text-2xl font-bold text-blue-400">&lt;60s</div>
            <div className="text-sm text-gray-400">Avg Pipeline Time</div>
          </div>
          <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
            <div className="text-2xl font-bold text-yellow-400">100%</div>
            <div className="text-sm text-gray-400">Audit Trail</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 justify-center pt-4">
          {["LangGraph", "Claude", "FastAPI", "Next.js", "PostgreSQL", "Celery", "Pinecone", "Docker"].map((tech) => (
            <span key={tech} className="px-2 py-1 bg-gray-800 text-gray-400 text-xs rounded border border-gray-700">
              {tech}
            </span>
          ))}
        </div>
      </div>
    </main>
  );
}
