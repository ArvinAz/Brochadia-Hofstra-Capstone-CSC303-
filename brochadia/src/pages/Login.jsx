import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import './Login.css'
import { storeUserId } from '../utils/authStorage'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const json = await res.json()
      if (!res.ok || !json.success) {
        setError(json.message || 'Login failed')
        return
      }
      if (!json.userId) {
        setError('Login failed: missing user id')
        return
      }
      storeUserId(json.userId)
      if (onLoginSuccess) onLoginSuccess()
      navigate('/')
    } catch (err) {
      setError('Network error while logging in')
    } finally {
      setLoading(false)
    }
  }
  return (
    <main className="login-page">
      <div className="login-container">
        <h1>Welcome back</h1>
        <p className="login-subtitle">Sign in to continue planning your trip</p>
        {error && <p className="login-error">{error}</p>}
        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Logging in…' : 'Log in'}
          </button>
        </form>
        <p className="login-signup">
          Don&apos;t have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </main>
  )
}

export default Login
