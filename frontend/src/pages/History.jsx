import { useState, useEffect, useCallback } from 'react'
import HistoryTable from '../components/HistoryTable'
import { apiFetch } from '../lib/api'

export default function History() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400)
    return () => clearTimeout(t)
  }, [search])

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ limit: '50' })
      if (debouncedSearch) params.set('company', debouncedSearch)
      const res = await apiFetch(`/history?${params}`)
      if (!res.ok) throw new Error('Failed to fetch history')
      const data = await res.json()
      setRecords(data.records || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [debouncedSearch])

  const fetchStats = async () => {
    try {
      const res = await apiFetch('/stats')
      if (res.ok) setStats(await res.json())
    } catch {}
  }

  useEffect(() => { fetchHistory(); fetchStats() }, [fetchHistory])

  const handleDelete = async (id) => {
    try {
      await apiFetch(`/record/${id}`, { method: 'DELETE' })
      setRecords(prev => prev.filter(r => r.id !== id))
    } catch {}
  }

  const STAT_CARDS = stats ? [
    { label: 'Total Runs',        value: stats.total_runs,          icon: '📊' },
    { label: 'Emails Ready',      value: stats.emails_ready,        icon: '✉️' },
    { label: 'Avg Score',         value: (stats.avg_score * 100).toFixed(0) + '%', icon: '🎯' },
    { label: 'Unique Companies',  value: stats.unique_companies,    icon: '🏢' },
  ] : []

  return (
    <div className="min-h-screen px-6 py-10 max-w-7xl mx-auto">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="animate-fade-in mb-8">
        <h1 className="text-4xl font-black text-white mb-2">Outreach History</h1>
        <p className="text-slate-500 text-sm">All agent runs — signals, scores, and generated emails</p>
      </div>

      {/* ── Stats row ───────────────────────────────────────────────────── */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {STAT_CARDS.map((s, i) => (
            <div key={s.label}
              className={`glass-card p-5 animate-fade-in-up`}
              style={{ animationDelay: `${i * 60}ms` }}>
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="text-2xl font-black text-white">{s.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Search + Refresh ────────────────────────────────────────────── */}
      <div className="animate-fade-in flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            className="input-field pl-10"
            placeholder="Filter by company name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <button
          id="refresh-history-btn"
          onClick={fetchHistory}
          className="btn-ghost flex-shrink-0">
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {error && (
        <div className="mb-4 rounded-xl p-4 text-sm text-red-400"
          style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)' }}>
          {error}
        </div>
      )}

      {/* ── Table ───────────────────────────────────────────────────────── */}
      {loading ? (
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="skeleton h-16 rounded-xl" />
          ))}
        </div>
      ) : (
        <HistoryTable records={records} onDelete={handleDelete} />
      )}
    </div>
  )
}
