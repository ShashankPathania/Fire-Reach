import { useEffect, useState } from 'react'

const LABELS = {
  hiring:    { label: 'Hiring Signal',    icon: '👥', weight: '40%' },
  funding:   { label: 'Funding Signal',   icon: '💰', weight: '30%' },
  expansion: { label: 'Expansion Signal', icon: '🌍', weight: '20%' },
  tech_stack:{ label: 'Tech Stack',       icon: '⚙️',  weight: '10%' },
}

function ScoreRing({ score }) {
  const [animated, setAnimated] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(score), 100)
    return () => clearTimeout(timer)
  }, [score])

  const radius = 52
  const circumference = 2 * Math.PI * radius
  const progress = circumference - animated * circumference
  const color = score >= 0.75 ? '#FF5A00' : score >= 0.5 ? '#F59E0B' : '#475569'
  const glow  = score >= 0.75 ? '0 0 20px rgba(255,90,0,0.5)' : score >= 0.5 ? '0 0 20px rgba(245,158,11,0.4)' : 'none'

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="130" height="130" className="-rotate-90">
        {/* Track */}
        <circle cx="65" cy="65" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        {/* Progress */}
        <circle cx="65" cy="65" r={radius} fill="none"
          stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={progress}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.34,1.56,0.64,1), filter 0.5s ease', filter: `drop-shadow(${glow})` }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-white" style={{ color }}>
          {Math.round(score * 100)}
        </span>
        <span className="text-xs text-slate-500 font-medium">/ 100</span>
      </div>
    </div>
  )
}

function BreakdownBar({ label, icon, weight, value }) {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setWidth(value * 100), 200)
    return () => clearTimeout(t)
  }, [value])

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-slate-400">
          <span>{icon}</span>
          <span>{label}</span>
          <span className="text-slate-600">({weight})</span>
        </span>
        <span className="font-semibold text-slate-300">{Math.round(value * 100)}%</span>
      </div>
      <div className="confidence-bar">
        <div className="confidence-bar-fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  )
}

export default function ScoreDisplay({ score = 0, breakdown = {} }) {
  const level = score >= 0.75 ? '🔥 High' : score >= 0.5 ? '⚡ Medium' : '❄️ Low'

  return (
    <div className="glass-card p-6">
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-5">
        Opportunity Score
      </div>
      <div className="flex items-center gap-6 mb-6">
        <ScoreRing score={score} />
        <div>
          <div className="text-2xl font-bold text-white mb-1">{level} Opportunity</div>
          <p className="text-xs text-slate-500 leading-relaxed max-w-48">
            {score >= 0.75
              ? 'Strong signals detected. Highly recommended for outreach.'
              : score >= 0.5
              ? 'Moderate signals. Email generated and ready.'
              : 'Insufficient signals. Outreach skipped to protect reputation.'}
          </p>
        </div>
      </div>

      {/* Breakdown bars */}
      <div className="space-y-3 pt-4 border-t border-white/[0.06]">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Score Breakdown
        </div>
        {Object.entries(LABELS).map(([key, meta]) => (
          <BreakdownBar
            key={key}
            label={meta.label}
            icon={meta.icon}
            weight={meta.weight}
            value={breakdown[key] ?? 0}
          />
        ))}
      </div>
    </div>
  )
}
