import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import ScoreDisplay from '../components/ScoreDisplay'
import SignalsCard from '../components/SignalsCard'
import EmailPreview from '../components/EmailPreview'

const TABS = [
  { id: 'overview', label: '📊 Overview' },
  { id: 'signals',  label: '📡 Signals' },
  { id: 'insights', label: '🧠 Insights' },
  { id: 'contacts', label: '👥 Contacts' },
  { id: 'email',    label: '✉️ Email' },
]

function StatusPill({ status }) {
  const label = {
    complete:    'Complete',
    email_ready: 'Email Ready',
    sent:        'Sent',
    stopped:     'Low Score — Stopped',
    failed:      'Failed',
  }[status] || status

  return <span className={`status-badge ${status}`}>{label}</span>
}

function OverviewTab({ result }) {
  const score = result.score ?? 0
  const threshold = result.score_threshold ?? 0.5
  const breakdown = result.score_breakdown ?? {}

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Score + strategy row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ScoreDisplay score={score} breakdown={breakdown} />

        <div className="glass-card p-6">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Outreach Strategy
          </div>
          {result.strategy ? (
            <p className="text-base text-white leading-relaxed">{result.strategy}</p>
          ) : (
            <p className="text-sm text-slate-500 italic">
              {score < threshold
                ? 'Score too low — outreach skipped to protect sender reputation.'
                : 'Strategy not generated.'}
            </p>
          )}

          {/* Decision explanation */}
          <div className="mt-4 pt-4 border-t border-white/[0.06]">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <div className={`w-1.5 h-1.5 rounded-full ${score >= threshold ? 'bg-orange-500' : 'bg-slate-600'}`} />
              {score >= threshold
                ? `Score ${score.toFixed(2)} ≥ ${threshold.toFixed(2)} → Proceeded with email generation`
                : `Score ${score.toFixed(2)} < ${threshold.toFixed(2)} → Stopped (insufficient signals)`}
            </div>
          </div>
        </div>
      </div>

      {/* Signals quick view */}
      {result.signals && Object.keys(result.signals).length > 0 && (
        <div className="glass-card p-6">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
            Detected Signals
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(result.signals).map(([type, data]) => (
              <div key={type}
                className="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium"
                style={{ background: 'rgba(255,90,0,0.08)', border: '1px solid rgba(255,90,0,0.15)', color: '#FF9A00' }}>
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                {type.replace('_', ' ')}
                <span className="opacity-60">({Math.round((data?.confidence ?? 0) * 100)}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function InsightsTab({ insights }) {
  const paragraphs = (insights || '').split('\n\n').filter(Boolean)

  return (
    <div className="glass-card p-8 animate-fade-in">
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-6">
        Account Brief — LLM Analysis
      </div>
      {paragraphs.length > 0 ? (
        <div className="space-y-5">
          {paragraphs.map((para, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
                style={{ background: 'rgba(255,90,0,0.15)', color: '#FF7A24' }}>
                {i + 1}
              </div>
              <p className="text-slate-300 leading-relaxed flex-1">{para}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-slate-500 italic">No insights generated.</p>
      )}
    </div>
  )
}

function ContactsTab({ contacts = [] }) {
  if (!contacts.length) {
    return (
      <div className="glass-card p-10 text-center text-slate-500 animate-fade-in">
        No contacts were discovered for this company.
      </div>
    )
  }

  return (
    <div className="glass-card p-6 space-y-4 animate-fade-in">
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
        Discovered Contacts
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-xs uppercase text-slate-500 border-b border-white/[0.06]">
            <tr>
              <th className="text-left py-2 pr-4 font-semibold">Name</th>
              <th className="text-left py-2 pr-4 font-semibold">Title</th>
              <th className="text-left py-2 pr-4 font-semibold">Email</th>
              <th className="text-left py-2 pr-4 font-semibold">Seniority</th>
              <th className="text-left py-2 pr-4 font-semibold">Confidence</th>
              <th className="text-left py-2 pr-4 font-semibold">Source</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((c) => (
              <tr key={c.email} className="border-b border-white/[0.03] last:border-0">
                <td className="py-2 pr-4 text-slate-200">
                  {c.name || '—'}
                </td>
                <td className="py-2 pr-4 text-slate-300">
                  {c.title || 'Unknown'}
                </td>
                <td className="py-2 pr-4">
                  <span className="font-mono text-xs text-slate-200">{c.email}</span>
                </td>
                <td className="py-2 pr-4 text-slate-400 capitalize">
                  {c.seniority || 'unknown'}
                </td>
                <td className="py-2 pr-4 text-slate-300">
                  {c.confidence != null ? `${Math.round((c.confidence || 0) * 100)}%` : '—'}
                </td>
                <td className="py-2 pr-4 text-slate-500 capitalize">
                  {c.source || 'hunter'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">
        Top {contacts.length} contacts ranked by title, seniority, confidence, and whether the inbox is generic.
      </p>
    </div>
  )
}

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')

  const result = location.state?.result
  useEffect(() => {
    if (!result) navigate('/')
  }, [result, navigate])

  if (!result) return null

  return (
    <div className="min-h-screen px-6 py-10 max-w-6xl mx-auto">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="animate-fade-in flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link to="/" className="btn-ghost text-sm px-3 py-1.5">
              ← Back
            </Link>
            <StatusPill status={result.status} />
          </div>
          <h1 className="text-4xl font-black text-white">
            {result.company}
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-lg truncate">
            ICP: {result.icp}
          </p>
        </div>

        {/* Score badge large */}
        <div className="flex-shrink-0">
          <div className={`score-badge text-lg px-5 py-2.5 ${
            result.score >= 0.75 ? 'high' : result.score >= 0.5 ? 'medium' : 'low'
          }`}>
            <span>
              {result.score >= 0.75 ? '🔥' : result.score >= 0.5 ? '⚡' : '❄️'}
            </span>
            <span className="font-black text-xl">{(result.score * 100).toFixed(0)}</span>
            <span className="text-sm opacity-70">/100</span>
          </div>
        </div>
      </div>

      {/* ── Tabs ────────────────────────────────────────────────────────── */}
      <div className="animate-fade-in flex items-center gap-1 mb-6 p-1 rounded-xl w-fit"
        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
        {TABS.map(tab => (
          <button key={tab.id}
            id={`tab-${tab.id}`}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ─────────────────────────────────────────────────── */}
      <div className="animate-fade-in">
        {activeTab === 'overview' && <OverviewTab result={result} />}
        {activeTab === 'signals'  && (
          <div className="space-y-4 animate-fade-in">
            {result.signals && Object.keys(result.signals).length > 0 ? (
              Object.entries(result.signals).map(([type, data]) => (
                <SignalsCard key={type} type={type} data={data} />
              ))
            ) : (
              <div className="glass-card p-12 text-center text-slate-500">
                No signals detected for this company.
              </div>
            )}
          </div>
        )}
        {activeTab === 'insights' && <InsightsTab insights={result.insights} />}
        {activeTab === 'contacts' && (
          <ContactsTab contacts={result.contact_candidates || []} />
        )}
        {activeTab === 'email'    && (
          <EmailPreview
            company={result.company}
            subject={result.email?.subject}
            body={result.email?.body}
            wordCount={result.email?.word_count}
            defaultRecipient={result.recipient_email}
            contactCandidates={result.contact_candidates}
          />
        )}
      </div>
    </div>
  )
}
