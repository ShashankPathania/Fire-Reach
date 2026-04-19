import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const from = location.state?.from || '/'

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-6 py-16 max-w-md mx-auto">
      <div className="glass-card p-8 animate-fade-in">
        <h1 className="text-3xl font-black text-white mb-2">Welcome back</h1>
        <p className="text-slate-500 text-sm mb-6">Sign in to continue to FireReach.</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <input className="input-field" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input className="input-field" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button className="btn-fire w-full" disabled={loading}>{loading ? 'Signing in...' : 'Login'}</button>
        </form>
        <p className="text-sm text-slate-500 mt-5">
          New here? <Link to="/signup" className="text-orange-400 hover:text-orange-300">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
