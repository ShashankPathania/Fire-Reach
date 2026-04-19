import { useState } from 'react'

const SIGNAL_META = {
  funding: {
    icon: '💰',
    label: 'Funding',
    color: 'rgba(16,185,129,0.15)',
    border: 'rgba(16,185,129,0.25)',
    textColor: '#6EE7B7',
    fields: [
      { key: 'amount',  label: 'Amount' },
      { key: 'round',   label: 'Round' },
      { key: 'status',  label: 'Status' },
      { key: 'date',    label: 'Date' },
    ],
  },
  hiring: {
    icon: '👥',
    label: 'Hiring',
    color: 'rgba(59,130,246,0.12)',
    border: 'rgba(59,130,246,0.25)',
    textColor: '#93C5FD',
    fields: [
      { key: 'open_roles',   label: 'Open Roles', format: v => v ? `${v}+ positions` : null },
      { key: 'departments',  label: 'Departments', format: v => Array.isArray(v) ? v.join(', ') : v },
      { key: 'growth_rate',  label: 'Growth Rate' },
    ],
  },
  expansion: {
    icon: '🌍',
    label: 'Expansion',
    color: 'rgba(139,92,246,0.12)',
    border: 'rgba(139,92,246,0.25)',
    textColor: '#C4B5FD',
    fields: [
      { key: 'regions',     label: 'Regions',     format: v => Array.isArray(v) ? v.join(', ') : v },
      { key: 'description', label: 'Description' },
    ],
  },
  tech_stack: {
    icon: '⚙️',
    label: 'Tech Stack',
    color: 'rgba(245,158,11,0.10)',
    border: 'rgba(245,158,11,0.2)',
    textColor: '#FCD34D',
    fields: [
      { key: 'identified', label: 'Technologies', format: v => Array.isArray(v) ? v.join(' · ') : v },
      { key: 'changes',    label: 'Changes' },
    ],
  },
  leadership: {
    icon: '👤',
    label: 'Leadership',
    color: 'rgba(236,72,153,0.10)',
    border: 'rgba(236,72,153,0.2)',
    textColor: '#F9A8D4',
    fields: [
      { key: 'description', label: 'Detail' },
      { key: 'headline',    label: 'Headline' },
    ],
  },
  news: {
    icon: '📰',
    label: 'News',
    color: 'rgba(255,255,255,0.04)',
    border: 'rgba(255,255,255,0.08)',
    textColor: '#94A3B8',
    fields: [
      { key: 'headline', label: 'Headline' },
      { key: 'snippet',  label: 'Snippet' },
      { key: 'date',     label: 'Date' },
    ],
  },
}

export default function SignalsCard({ type, data }) {
  const [expanded, setExpanded] = useState(true)
  const meta = SIGNAL_META[type] ?? {
    icon: '📌', label: type, color: 'rgba(255,255,255,0.04)',
    border: 'rgba(255,255,255,0.08)', textColor: '#94A3B8', fields: [],
  }

  const confidence = data?.confidence ?? 0
  const confPct = Math.round(confidence * 100)

  return (
    <div className="glass-card p-5 animate-fade-in"
      style={{ borderColor: meta.border }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
            style={{ background: meta.color, border: `1px solid ${meta.border}` }}>
            {meta.icon}
          </div>
          <div>
            <div className="font-semibold text-white text-sm">{meta.label} Signal</div>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="confidence-bar w-24">
                <div className="confidence-bar-fill" style={{ width: `${confPct}%` }} />
              </div>
              <span className="text-xs font-medium" style={{ color: meta.textColor }}>
                {confPct}% confidence
              </span>
            </div>
          </div>
        </div>

        <button onClick={() => setExpanded(!expanded)}
          className="text-slate-500 hover:text-slate-300 transition-colors p-1">
          <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? '' : '-rotate-90'}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Fields */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/[0.05] space-y-2 animate-fade-in">
          {meta.fields.map(({ key, label, format }) => {
            const raw = data?.[key]
            if (raw === null || raw === undefined || raw === '' ||
                (Array.isArray(raw) && raw.length === 0)) return null
            const display = format ? format(raw) : String(raw)
            if (!display) return null

            return (
              <div key={key} className="flex items-baseline gap-3 text-sm">
                <span className="text-slate-500 text-xs w-24 flex-shrink-0">{label}</span>
                <span className="text-slate-200 flex-1">{display}</span>
              </div>
            )
          })}

          {/* Source link */}
          {data?.source && (
            <div className="flex items-baseline gap-3 text-sm pt-1">
              <span className="text-slate-500 text-xs w-24 flex-shrink-0">Source</span>
              <a href={data.source} target="_blank" rel="noreferrer"
                className="text-xs truncate max-w-xs transition-colors"
                style={{ color: meta.textColor }}
                onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                onMouseLeave={e => e.target.style.textDecoration = 'none'}>
                {data.source.replace(/^https?:\/\//, '').split('/')[0]}
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
