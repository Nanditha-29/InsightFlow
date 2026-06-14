'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  listCompetitors,
  createCompetitor,
  Competitor,
} from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [competitorName, setCompetitorName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadCompetitors();
  }, []);

  async function loadCompetitors() {
    setLoading(true);
    try {
      const data = await listCompetitors();
      setCompetitors(data.competitors);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!competitorName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const comp = await createCompetitor(competitorName.trim());
      setCompetitors(prev => [comp, ...prev]);
      setShowCreate(false);
      setCompetitorName('');
      // Navigate to workspace
      router.push(`/competitors/${comp.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  }

  const filteredCompetitors = search
    ? competitors.filter(c => c.name.toLowerCase().includes(search.toLowerCase()))
    : competitors;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-200">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  InsightFlow
                </h1>
                <p className="text-xs text-gray-400 -mt-0.5">Competitive Intelligence OS</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 text-sm font-medium transition-all shadow-md shadow-indigo-200 hover:shadow-lg"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Competitor
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="text-center mb-10">
          <h2 className="text-4xl font-bold text-gray-900 mb-3">
            Your Competitive Intelligence Hub
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Track competitors, discover trusted sources, generate insights, and ask questions. 
            Every competitor gets its own intelligence workspace.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
            <span>⚠️</span>
            <span className="text-sm">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">✕</button>
          </div>
        )}

        {/* Search */}
        {competitors.length > 0 && (
          <div className="mb-6">
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search competitors..."
              className="w-full max-w-md px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm bg-white/80"
            />
          </div>
        )}

        {/* Empty State */}
        {!loading && competitors.length === 0 && (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No competitors yet</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Create your first competitor workspace. InsightFlow will automatically discover trusted sources and extract intelligence.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 font-medium transition-all shadow-lg shadow-indigo-200"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Your First Competitor
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500">Loading competitors...</p>
          </div>
        )}

        {/* Competitor Grid */}
        {!loading && competitors.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCompetitors.map(comp => (
              <button
                key={comp.id}
                onClick={() => router.push(`/competitors/${comp.id}`)}
                className="group relative bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-indigo-300 hover:shadow-lg transition-all card-hover"
              >
                {/* Gradient accent */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="flex items-start justify-between mb-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center text-lg font-bold text-indigo-600">
                    {comp.name.charAt(0)}
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    comp.signal_count > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {comp.signal_count} signals
                  </span>
                </div>

                <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                  {comp.name}
                </h3>
                {comp.website && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate">{comp.website}</p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {comp.source_count} sources · {comp.report_count} reports
                </p>

                <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
                  <span>Updated {new Date(comp.last_updated).toLocaleDateString()}</span>
                  <span className="text-gray-300">·</span>
                  <span className="flex items-center gap-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      comp.source_count > 0 ? 'bg-green-400' : 'bg-gray-300'
                    }`} />
                    Active
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Create Competitor</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              Enter a company name. InsightFlow will automatically discover trusted sources and build an intelligence workspace.
            </p>

            <input
              type="text"
              value={competitorName}
              onChange={e => setCompetitorName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              placeholder="e.g., OpenAI, Anthropic, Google DeepMind"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm mb-4"
              autoFocus
            />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-xs mb-4">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating || !competitorName.trim()}
                className="flex-1 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-sm font-medium transition-all flex items-center justify-center gap-2"
              >
                {creating ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Discovering sources...
                  </>
                ) : (
                  'Create Workspace'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white/80 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-400">
              InsightFlow — AI Competitive Intelligence OS
            </p>
            <p className="text-xs text-gray-400">
              v1.0 • Built with FastAPI + Next.js
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
