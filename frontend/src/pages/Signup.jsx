import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await signup({ name, email, password })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-6 py-16 max-w-md mx-auto">
      <div className="glass-card p-8 animate-fade-in">
        <h1 className="text-3xl font-black text-white mb-2">Create account</h1>
        <p className="text-slate-500 text-sm mb-6">Set up your FireReach workspace.</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <input className="input-field" type="text" placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input className="input-field" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input className="input-field" type="password" placeholder="Password (min 8 chars)" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          <input className="input-field" type="password" placeholder="Confirm password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button className="btn-fire w-full" disabled={loading}>{loading ? 'Creating account...' : 'Sign up'}</button>
        </form>
        <p className="text-sm text-slate-500 mt-5">
          Already have an account? <Link to="/login" className="text-orange-400 hover:text-orange-300">Login</Link>
        </p>
      </div>
    </div>
  )
}
