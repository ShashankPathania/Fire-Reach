import { useState } from 'react'

function StatusBadge({ status }) {
  const map = {
    complete:    { label: 'Complete',   cls: 'complete' },
    email_ready: { label: 'Ready',      cls: 'email_ready' },
    sent:        { label: 'Sent',       cls: 'sent' },
    stopped:     { label: 'Stopped',    cls: 'stopped' },
    failed:      { label: 'Failed',     cls: 'failed' },
  }
  const { label, cls } = map[status] ?? { label: status, cls: 'stopped' }
  return <span className={`status-badge ${cls}`}>{label}</span>
}

function ScorePill({ score }) {
  if (score === null || score === undefined) return <span className="text-slate-600 text-xs">—</span>
  const pct = Math.round(score * 100)
  const cls = score >= 0.75 ? 'high' : score >= 0.5 ? 'medium' : 'low'
  return (
    <span className={`score-badge ${cls} text-xs`}>
      {score >= 0.75 ? '🔥' : score >= 0.5 ? '⚡' : '❄️'} {pct}
    </span>
  )
}

function EmailModal({ record, onClose }) {
  const [copied, setCopied] = useState(false)

  const copyEmail = async () => {
    const text = `Subject: ${record.email_subject}\n\n${record.email_body}`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="glass-card w-full max-w-2xl p-8 animate-fade-in-up">
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-xs text-slate-500 mb-1">Generated Email</div>
            <h3 className="text-lg font-bold text-white">{record.company}</h3>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {record.email_subject && (
            <div className="rounded-xl p-4"
              style={{ background: 'rgba(255,90,0,0.06)', border: '1px solid rgba(255,90,0,0.15)' }}>
              <div className="text-xs text-slate-500 mb-1">Subject</div>
              <p className="text-white font-semibold">{record.email_subject}</p>
            </div>
          )}
          {record.email_body && (
            <div className="rounded-xl p-4"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="text-xs text-slate-500 mb-2">Body</div>
              <p className="text-slate-300 text-sm leading-relaxed font-mono whitespace-pre-wrap">
                {record.email_body}
              </p>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={copyEmail} className="btn-ghost text-sm flex-1">
            {copied ? '✓ Copied!' : 'Copy Email'}
          </button>
          <button onClick={onClose} className="btn-ghost text-sm">Close</button>
        </div>
      </div>
    </div>
  )
}

export default function HistoryTable({ records, onDelete }) {
  const [selectedRecord, setSelectedRecord] = useState(null)

  if (!records || records.length === 0) {
    return (
      <div className="glass-card p-16 text-center">
        <div className="text-5xl mb-4">📭</div>
        <p className="text-slate-400 font-medium">No outreach history yet</p>
        <p className="text-xs text-slate-600 mt-1">Run your first analysis to see results here</p>
      </div>
    )
  }

  const fmt = (iso) => {
    if (!iso) return '—'
    try {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      }).format(new Date(iso))
    } catch { return iso }
  }

  return (
    <>
      {/* Modal */}
      {selectedRecord && (
        <EmailModal record={selectedRecord} onClose={() => setSelectedRecord(null)} />
      )}

      {/* Table */}
      <div className="glass-card overflow-hidden animate-fade-in">
        {/* Desktop view */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                {['Company', 'Score', 'Status', 'Signals', 'Date', 'Actions'].map(h => (
                  <th key={h} className="text-left px-5 py-3.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={r.id}
                  className="transition-colors group"
                  style={{
                    borderBottom: i < records.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>

                  <td className="px-5 py-4">
                    <div className="font-semibold text-white">{r.company}</div>
                    <div className="text-xs text-slate-600 truncate max-w-48">{r.icp?.slice(0, 60)}</div>
                  </td>

                  <td className="px-5 py-4">
                    <ScorePill score={r.score} />
                  </td>

                  <td className="px-5 py-4">
                    <StatusBadge status={r.status} />
                  </td>

                  <td className="px-5 py-4">
                    <div className="flex flex-wrap gap-1">
                      {r.cleaned_signals && Object.keys(r.cleaned_signals).map(sig => (
                        <span key={sig}
                          className="text-xs rounded-full px-2 py-0.5"
                          style={{ background: 'rgba(255,90,0,0.08)', color: '#FF9A00', border: '1px solid rgba(255,90,0,0.15)' }}>
                          {sig.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-xs text-slate-500 whitespace-nowrap">
                    {fmt(r.created_at)}
                  </td>

                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {r.email_body && (
                        <button
                          onClick={() => setSelectedRecord(r)}
                          className="text-xs btn-ghost py-1.5 px-3">
                          View Email
                        </button>
                      )}
                      <button
                        onClick={() => onDelete?.(r.id)}
                        className="p-1.5 text-slate-600 hover:text-red-400 transition-colors rounded-lg hover:bg-red-400/10">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden divide-y divide-white/[0.04]">
          {records.map(r => (
            <div key={r.id} className="p-5 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-white">{r.company}</div>
                  <div className="text-xs text-slate-600 mt-0.5">{fmt(r.created_at)}</div>
                </div>
                <ScorePill score={r.score} />
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={r.status} />
              </div>
              {r.email_body && (
                <button onClick={() => setSelectedRecord(r)}
                  className="btn-ghost text-xs py-1.5 w-full">
                  View Email
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
