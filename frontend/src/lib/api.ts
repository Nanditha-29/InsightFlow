/**
 * InsightFlow API client — Competitor Intelligence Platform
 */

const API_BASE = '/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API ${res.status}: ${error}`);
  }

  return res.json();
}

// ========================
// Types
// ========================

export interface Competitor {
  id: string;
  name: string;
  industry: string;
  description: string;
  website: string | null;
  status: string;
  created_at: string;
  last_updated: string;
  source_count: number;
  signal_count: number;
  report_count: number;
}

export interface Source {
  id: string;
  url: string;
  title: string;
  source_type: string;
  category: string;
  trust_score: number;
  is_active: boolean;
  last_checked: string | null;
}

export interface Signal {
  id: string;
  signal_type: string;
  title: string;
  summary: string;
  detail: string | null;
  confidence: number;
  source_url: string | null;
  tags: string[] | null;
  detected_at: string;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description: string | null;
  event_date: string | null;
  source_url: string | null;
  confidence: number;
  created_at: string;
}

export interface Report {
  id: string;
  report_type: string;
  title: string;
  executive_summary: string | null;
  report_data: any;
  version: number;
  generated_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  citations: Citation[] | null;
  confidence: number | null;
  timestamp: string;
}

export interface Citation {
  source: string;
  evidence: string;
  confidence: number;
}

export interface DashboardData {
  competitor_name: string;
  competitor_id: string;
  industry: string;
  website: string | null;
  last_updated: string;
  stats: {
    total_sources: number;
    total_signals: number;
    total_reports: number;
    total_chat_sessions: number;
    total_timeline_events: number;
    average_trust_score: number;
    signal_types: string[];
  };
  recent_signals: Signal[];
}

export interface RecheckResult {
  status: string;
  new_signals: number;
  changed_signals: number;
  removed_signals: number;
  total_signals: number;
}

// ========================
// Competitor endpoints
// ========================

export async function createCompetitor(name: string): Promise<Competitor> {
  return request<Competitor>('/competitors', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function listCompetitors(search?: string): Promise<{ competitors: Competitor[]; total: number }> {
  const params = search ? `?search=${encodeURIComponent(search)}` : '';
  return request<{ competitors: Competitor[]; total: number }>(`/competitors${params}`);
}

export async function getCompetitor(id: string): Promise<Competitor> {
  return request<Competitor>(`/competitors/${id}`);
}

export async function deleteCompetitor(id: string): Promise<{ status: string; id: string }> {
  return request<{ status: string; id: string }>(`/competitors/${id}`, { method: 'DELETE' });
}

export async function getDashboard(id: string): Promise<DashboardData> {
  return request<DashboardData>(`/competitors/${id}/dashboard`);
}

// ========================
// Sources
// ========================

export async function getSources(competitorId: string): Promise<Source[]> {
  return request<Source[]>(`/competitors/${competitorId}/sources`);
}

// ========================
// Signals
// ========================

export async function getSignals(competitorId: string, signalType?: string, limit = 50): Promise<Signal[]> {
  const params = new URLSearchParams();
  if (signalType) params.set('signal_type', signalType);
  params.set('limit', String(limit));
  return request<Signal[]>(`/competitors/${competitorId}/signals?${params}`);
}

// ========================
// Timeline
// ========================

export async function getTimeline(competitorId: string): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/competitors/${competitorId}/timeline`);
}

// ========================
// Reports
// ========================

export async function generateReport(competitorId: string): Promise<Report> {
  return request<Report>(`/competitors/${competitorId}/reports/generate`, { method: 'POST' });
}

export async function getReports(competitorId: string): Promise<Report[]> {
  return request<Report[]>(`/competitors/${competitorId}/reports`);
}

// ========================
// Chat
// ========================

export async function createChatSession(competitorId: string): Promise<ChatSession> {
  return request<ChatSession>(`/competitors/${competitorId}/chat/sessions`, { method: 'POST' });
}

export async function getChatSessions(competitorId: string): Promise<ChatSession[]> {
  return request<ChatSession[]>(`/competitors/${competitorId}/chat/sessions`);
}

export async function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/competitors/chat/sessions/${sessionId}/messages`);
}

export async function sendChatMessage(sessionId: string, content: string): Promise<{
  answer: string;
  citations: Citation[];
  confidence: number;
  message_id: string;
}> {
  return request(`/competitors/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

// ========================
// Recheck
// ========================

export async function recheckCompetitor(competitorId: string): Promise<RecheckResult> {
  return request<RecheckResult>(`/competitors/${competitorId}/recheck`, { method: 'POST' });
}

// ========================
// Compare
// ========================

export async function compareCompetitors(competitorIds: string[]): Promise<any> {
  return request('/competitors/compare', {
    method: 'POST',
    body: JSON.stringify({ competitor_ids: competitorIds }),
  });
}
