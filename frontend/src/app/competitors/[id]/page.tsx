'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getCompetitor,
  getDashboard,
  getSources,
  getSignals,
  getTimeline,
  getReports,
  generateReport,
  getChatSessions,
  createChatSession,
  getChatMessages,
  sendChatMessage,
  recheckCompetitor,
  compareCompetitors,
  Competitor,
  DashboardData,
  Source,
  Signal,
  TimelineEvent,
  Report,
  ChatSession,
  ChatMessage,
  Citation,
} from '@/lib/api';

type Tab = 'overview' | 'signals' | 'sources' | 'timeline' | 'reports' | 'chat';

export default function CompetitorWorkspace() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [competitor, setCompetitor] = useState<Competitor | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [signalFilter, setSignalFilter] = useState<string>('');

  // Chat state
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [showChatSessions, setShowChatSessions] = useState(false);

  // Recheck state
  const [recheckLoading, setRecheckLoading] = useState(false);
  const [recheckResult, setRecheckResult] = useState<any>(null);

  // Generate report state
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    if (id) loadAll();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'chat') loadChatSessions();
    if (activeTab === 'signals') loadSignals();
    if (activeTab === 'timeline') loadTimeline();
    if (activeTab === 'reports') loadReports();
    if (activeTab === 'sources') loadSources();
  }, [activeTab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  async function loadAll() {
    setLoading(true);
    try {
      const [comp, dash] = await Promise.all([
        getCompetitor(id),
        getDashboard(id),
      ]);
      setCompetitor(comp);
      setDashboard(dash);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadSources() {
    try { setSources(await getSources(id)); } catch (e: any) { setError(e.message); }
  }

  async function loadSignals(type?: string) {
    try {
      const data = await getSignals(id, type || signalFilter || undefined);
      setSignals(data);
    } catch (e: any) { setError(e.message); }
  }

  async function loadTimeline() {
    try { setTimeline(await getTimeline(id)); } catch (e: any) { setError(e.message); }
  }

  async function loadReports() {
    try { setReports(await getReports(id)); } catch (e: any) { setError(e.message); }
  }

  async function loadChatSessions() {
    try {
      const sessions = await getChatSessions(id);
      setChatSessions(sessions);
      if (sessions.length > 0 && !activeSession) {
        setActiveSession(sessions[0].id);
        const msgs = await getChatMessages(sessions[0].id);
        setChatMessages(msgs);
      }
    } catch (e: any) { setError(e.message); }
  }

  async function handleNewChat() {
    try {
      const session = await createChatSession(id);
      setChatSessions(prev => [session, ...prev]);
      setActiveSession(session.id);
      setChatMessages([]);
      setShowChatSessions(false);
    } catch (e: any) { setError(e.message); }
  }

  async function handleSelectSession(sessionId: string) {
    setActiveSession(sessionId);
    setShowChatSessions(false);
    try {
      const msgs = await getChatMessages(sessionId);
      setChatMessages(msgs);
    } catch (e: any) { setError(e.message); }
  }

  async function handleSendMessage() {
    if (!chatInput.trim() || !activeSession) return;
    setChatLoading(true);
    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: 'temp',
      role: 'user',
      content: chatInput,
      citations: null,
      confidence: null,
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, tempUserMsg]);
    const input = chatInput;
    setChatInput('');

    try {
      const result = await sendChatMessage(activeSession, input);
      const assistantMsg: ChatMessage = {
        id: result.message_id,
        role: 'assistant',
        content: result.answer,
        citations: result.citations,
        confidence: result.confidence,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev.filter(m => m.id !== 'temp'), assistantMsg]);
    } catch (e: any) {
      setChatMessages(prev => prev.filter(m => m.id !== 'temp'));
      setError(e.message);
    } finally {
      setChatLoading(false);
    }
  }

  async function handleRecheck() {
    setRecheckLoading(true);
    setRecheckResult(null);
    try {
      const result = await recheckCompetitor(id);
      setRecheckResult(result);
      await loadAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRecheckLoading(false);
    }
  }

  async function handleGenerateReport() {
    setReportLoading(true);
    try {
      await generateReport(id);
      await loadReports();
      setActiveTab('reports');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setReportLoading(false);
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
    });
  }

  function getSignalColor(type: string) {
    const colors: Record<string, string> = {
      product: 'bg-blue-100 text-blue-700',
      strategic: 'bg-purple-100 text-purple-700',
      financial: 'bg-green-100 text-green-700',
      hiring: 'bg-amber-100 text-amber-700',
      pricing: 'bg-pink-100 text-pink-700',
      market: 'bg-cyan-100 text-cyan-700',
      regulation: 'bg-red-100 text-red-700',
      general: 'bg-gray-100 text-gray-700',
    };
    return colors[type] || colors.general;
  }

  function getSourceIcon(type: string) {
    if (type.includes('official')) return '🏢';
    if (type.includes('social') || type.includes('linkedin') || type.includes('twitter')) return '🔗';
    if (type.includes('news') || type.includes('reuters') || type.includes('bloomberg')) return '📰';
    if (type.includes('sec') || type.includes('research')) return '📄';
    return '🌐';
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!competitor) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || 'Competitor not found'}</p>
          <button onClick={() => router.push('/')} className="text-indigo-600 hover:text-indigo-700 font-medium">
            ← Back to Home
          </button>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'signals', label: 'Signals', icon: '💡' },
    { id: 'sources', label: 'Sources', icon: '🔍' },
    { id: 'timeline', label: 'Timeline', icon: '📅' },
    { id: 'reports', label: 'Reports', icon: '📋' },
    { id: 'chat', label: 'Chat', icon: '💬' },
  ];

  const signalTypes = dashboard?.stats.signal_types || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button onClick={() => router.push('/')} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
                {competitor.name.charAt(0)}
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">{competitor.name}</h1>
                {competitor.website && (
                  <p className="text-xs text-gray-400">{competitor.website}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRecheck}
                disabled={recheckLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                <svg className={`w-4 h-4 ${recheckLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {recheckLoading ? 'Rechecking...' : 'Recheck'}
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={reportLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 transition-all"
              >
                {reportLoading ? 'Generating...' : 'Generate Report'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Recheck result banner */}
      {recheckResult && (
        <div className="bg-green-50 border-b border-green-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm text-green-800">
              <span>✅ Intelligence refreshed</span>
              <span className="text-green-600">+{recheckResult.new_signals} new</span>
              {recheckResult.changed_signals > 0 && <span className="text-amber-600">~{recheckResult.changed_signals} changed</span>}
              {recheckResult.removed_signals > 0 && <span className="text-red-600">-{recheckResult.removed_signals} removed</span>}
              <span className="text-green-600">· {recheckResult.total_signals} total signals</span>
            </div>
            <button onClick={() => setRecheckResult(null)} className="text-green-600 hover:text-green-800">✕</button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">✕</button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-1 overflow-x-auto" aria-label="Tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-1.5">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* ==================== OVERVIEW ==================== */}
        {activeTab === 'overview' && dashboard && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {[
                { label: 'Sources', value: dashboard.stats.total_sources, color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Signals', value: dashboard.stats.total_signals, color: 'text-purple-600', bg: 'bg-purple-50' },
                { label: 'Reports', value: dashboard.stats.total_reports, color: 'text-green-600', bg: 'bg-green-50' },
                { label: 'Chats', value: dashboard.stats.total_chat_sessions, color: 'text-amber-600', bg: 'bg-amber-50' },
                { label: 'Events', value: dashboard.stats.total_timeline_events, color: 'text-pink-600', bg: 'bg-pink-50' },
                { label: 'Trust Avg', value: `${(dashboard.stats.average_trust_score * 100).toFixed(0)}%`, color: 'text-cyan-600', bg: 'bg-cyan-50' },
              ].map(stat => (
                <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center card-hover">
                  <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                  <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Signal Types */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">Signal Categories</h3>
              <div className="flex flex-wrap gap-2">
                {signalTypes.map(type => (
                  <span key={type} className={`text-xs font-medium px-2.5 py-1 rounded-full ${getSignalColor(type)}`}>
                    {type}
                  </span>
                ))}
              </div>
            </div>

            {/* Recent Signals */}
            {dashboard.recent_signals.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm">Recent Intelligence</h3>
                <div className="space-y-2">
                  {dashboard.recent_signals.slice(0, 8).map(s => (
                    <div key={s.id} className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-gray-50 transition-colors">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full mt-0.5 ${getSignalColor(s.signal_type)}`}>
                        {s.signal_type}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">{s.title}</p>
                        <p className="text-xs text-gray-500 line-clamp-1">{s.summary}</p>
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{formatDate(s.detected_at)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== SIGNALS ==================== */}
        {activeTab === 'signals' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => { setSignalFilter(''); loadSignals(); }}
                className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${
                  !signalFilter ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              {signalTypes.map(type => (
                <button
                  key={type}
                  onClick={() => { setSignalFilter(type); loadSignals(type); }}
                  className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${
                    signalFilter === type ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              {signals.map(s => (
                <div key={s.id} className="bg-white rounded-lg border border-gray-200 p-4 card-hover">
                  <div className="flex items-start gap-2 mb-2">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getSignalColor(s.signal_type)}`}>
                      {s.signal_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      {(s.confidence * 100).toFixed(0)}% confidence
                    </span>
                    <span className="text-xs text-gray-400 ml-auto">{formatDate(s.detected_at)}</span>
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm mb-1">{s.title}</h4>
                  <p className="text-sm text-gray-600">{s.summary}</p>
                  {s.tags && s.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {s.tags.map(tag => (
                        <span key={tag} className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{tag}</span>
                      ))}
                    </div>
                  )}
                  {s.source_url && (
                    <a href={s.source_url} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-indigo-500 hover:text-indigo-700 mt-2 inline-block truncate max-w-full">
                      🔗 {s.source_url}
                    </a>
                  )}
                </div>
              ))}
              {signals.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <p>No intelligence signals yet. Click "Recheck" to discover signals or "Generate Report" to create a report.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== SOURCES ==================== */}
        {activeTab === 'sources' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">Trusted Sources ({sources.length})</h3>
              <span className="text-xs text-gray-400">Avg trust: {sources.length > 0 ? (sources.reduce((a, s) => a + s.trust_score, 0) / sources.length * 100).toFixed(0) : 0}%</span>
            </div>
            {sources.map(s => (
              <div key={s.id} className="bg-white rounded-lg border border-gray-200 p-4 card-hover">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <span className="text-lg mt-0.5">{getSourceIcon(s.source_type)}</span>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-gray-900 truncate">{s.title}</h4>
                      <a href={s.url} target="_blank" rel="noopener noreferrer"
                        className="text-xs text-indigo-500 hover:text-indigo-700 truncate block max-w-full">
                        {s.url}
                      </a>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{s.source_type}</span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{s.category}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0 ml-4">
                    <div className={`text-sm font-bold ${
                      s.trust_score >= 0.9 ? 'text-green-600' :
                      s.trust_score >= 0.7 ? 'text-amber-600' :
                      'text-gray-500'
                    }`}>
                      {(s.trust_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-400">trust</div>
                  </div>
                </div>
                {s.last_checked && (
                  <p className="text-xs text-gray-400 mt-2">Last checked: {formatDate(s.last_checked)}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ==================== TIMELINE ==================== */}
        {activeTab === 'timeline' && (
          <div className="space-y-4">
            {timeline.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-3">📅</div>
                <p>No timeline events yet. Intelligence signals with timeline events will appear here.</p>
              </div>
            ) : (
              <div className="timeline-line pl-8 space-y-5">
                {timeline.map((event, idx) => (
                  <div key={event.id} className="relative">
                    <div className={`absolute -left-8 mt-1.5 w-3 h-3 rounded-full border-2 border-white shadow ${
                      idx === 0 ? 'bg-indigo-500' : 'bg-purple-500'
                    }`} />
                    <div className="bg-white rounded-lg border border-gray-200 p-4 card-hover">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getSignalColor(event.event_type)}`}>
                          {event.event_type}
                        </span>
                        {event.event_date && (
                          <span className="text-xs text-gray-400">{formatDate(event.event_date)}</span>
                        )}
                        <span className="text-xs text-gray-400 ml-auto">
                          {(event.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                      <h4 className="font-semibold text-gray-900 text-sm">{event.title}</h4>
                      {event.description && (
                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                      )}
                      {event.source_url && (
                        <a href={event.source_url} target="_blank" rel="noopener noreferrer"
                          className="text-xs text-indigo-500 hover:text-indigo-700 mt-2 inline-block">
                          🔗 Source
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== REPORTS ==================== */}
        {activeTab === 'reports' && (
          <div className="space-y-4">
            {reports.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-3">📋</div>
                <p className="mb-4">No reports generated yet. Generate your first intelligence report.</p>
                <button
                  onClick={handleGenerateReport}
                  disabled={reportLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 text-sm font-medium disabled:opacity-50"
                >
                  {reportLoading ? 'Generating...' : 'Generate Report Now'}
                </button>
              </div>
            ) : (
              reports.map(report => (
                <div key={report.id} className="bg-white rounded-xl border border-gray-200 p-5 card-hover">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{report.title}</h3>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                          v{report.version}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {report.report_type} · {formatDate(report.generated_at)}
                      </p>
                    </div>
                  </div>

                  {report.executive_summary && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-1">Executive Summary</h4>
                      <p className="text-sm text-gray-600">{report.executive_summary}</p>
                    </div>
                  )}

                  {report.report_data?.swot && (
                    <div className="grid grid-cols-2 gap-3 mb-4">
                      {Object.entries(report.report_data.swot).map(([key, items]) => (
                        <div key={key} className={`p-3 rounded-lg ${
                          key === 'strengths' ? 'bg-green-50' :
                          key === 'weaknesses' ? 'bg-red-50' :
                          key === 'opportunities' ? 'bg-blue-50' : 'bg-amber-50'
                        }`}>
                          <h5 className="text-xs font-semibold text-gray-700 capitalize mb-1">{key}</h5>
                          <ul className="space-y-1">
                            {(items as string[]).slice(0, 3).map((item, i) => (
                              <li key={i} className="text-xs text-gray-600">• {item}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}

                  {report.report_data?.strategic_insights && report.report_data.strategic_insights.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Strategic Insights</h4>
                      {report.report_data.strategic_insights.map((si: any, i: number) => (
                        <div key={i} className="text-sm text-gray-600 mb-1">
                          <span className="font-medium text-gray-700">{si.area}:</span> {si.insight}
                        </div>
                      ))}
                    </div>
                  )}

                  {report.report_data?.risk_assessment && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <span className="text-xs font-medium text-gray-700">Risk: </span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        report.report_data.risk_assessment.overall_risk === 'low' ? 'bg-green-100 text-green-700' :
                        report.report_data.risk_assessment.overall_risk === 'medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {report.report_data.risk_assessment.overall_risk}
                      </span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* ==================== CHAT ==================== */}
        {activeTab === 'chat' && (
          <div className="flex gap-4 h-[calc(100vh-240px)]">
            {/* Session list sidebar */}
            <div className="w-64 flex-shrink-0 hidden sm:block">
              <div className="bg-white rounded-xl border border-gray-200 h-full flex flex-col">
                <div className="p-3 border-b border-gray-100">
                  <button
                    onClick={handleNewChat}
                    className="w-full px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                  >
                    + New Chat
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {chatSessions.map(s => (
                    <button
                      key={s.id}
                      onClick={() => handleSelectSession(s.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        activeSession === s.id
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <p className="truncate font-medium">{s.title}</p>
                      <p className="text-xs text-gray-400">{s.message_count} messages</p>
                    </button>
                  ))}
                  {chatSessions.length === 0 && (
                    <p className="text-xs text-gray-400 p-3 text-center">No conversations yet</p>
                  )}
                </div>
              </div>
            </div>

            {/* Chat area */}
            <div className="flex-1 flex flex-col bg-white rounded-xl border border-gray-200">
              {!activeSession ? (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-3">💬</div>
                    <p className="mb-4">Start a conversation about {competitor.name}</p>
                    <button
                      onClick={handleNewChat}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium"
                    >
                      Start Chat
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Mobile session picker */}
                  <div className="sm:hidden p-3 border-b border-gray-100 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Chat</span>
                    <div className="flex gap-2">
                      <button onClick={() => setShowChatSessions(!showChatSessions)} className="text-xs text-gray-500 hover:text-gray-700">
                        {showChatSessions ? 'Hide sessions' : `${chatSessions.length} sessions`}
                      </button>
                      <button onClick={handleNewChat} className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                        + New
                      </button>
                    </div>
                  </div>
                  {showChatSessions && (
                    <div className="sm:hidden p-2 border-b border-gray-100 space-y-1 max-h-40 overflow-y-auto">
                      {chatSessions.map(s => (
                        <button
                          key={s.id}
                          onClick={() => handleSelectSession(s.id)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                            activeSession === s.id ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <p className="truncate">{s.title}</p>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatMessages.map(m => (
                      <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] ${
                          m.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-3'
                            : 'bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm px-4 py-3'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                          {m.role === 'assistant' && m.confidence !== null && (
                            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-200">
                              <span className="text-xs text-gray-500">
                                Confidence: {(m.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                          {/* Citations */}
                          {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-200 space-y-1.5">
                              <p className="text-xs font-medium text-gray-500">Sources:</p>
                              {m.citations.map((c, i) => (
                                <div key={i} className="text-xs bg-white/50 rounded-lg p-2">
                                  <p className="text-gray-700">{c.evidence}</p>
                                  <p className="text-gray-400 mt-0.5 truncate">📎 {c.source}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Input */}
                  <div className="border-t border-gray-200 p-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                        placeholder={`Ask about ${competitor.name}...`}
                        className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        disabled={chatLoading}
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={chatLoading || !chatInput.trim()}
                        className="px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
