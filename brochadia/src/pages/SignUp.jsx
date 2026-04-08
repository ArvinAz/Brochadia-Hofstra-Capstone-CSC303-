import { Link, useNavigate } from 'react-router-dom'
import './SignUp.css'
import { useState } from 'react'
import { getSignupDraft, storeSignupDraft } from '../utils/signupDraftStorage'

function SignUp() {
  const [email, setEmail] = useState(() => getSignupDraft()?.email ?? '')
  const [password, setPassword] = useState(() => getSignupDraft()?.password ?? '')
  const [full_name, setFull_name] = useState(() => getSignupDraft()?.full_name ?? '')
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    const signupDraft = {
      email: email.trim(),
      password,
      full_name: full_name.trim(),
    }

    if (!signupDraft.full_name || !signupDraft.email || !signupDraft.password) {
      setError('Full name, email, and password are required')
      return
    }

    storeSignupDraft(signupDraft)
    navigate('/signup/questionnaire', { state: signupDraft })
  }

  return (
    <main className="signup-page">
      <div className="signup-container">
        <h1>Create your account</h1>
        <p className="signup-subtitle">Start planning your next adventure</p>
        {error && <p className="signup-error">{error}</p>}
        <form className="signup-form" onSubmit={handleSubmit}>
          <label htmlFor="name">Full name</label>
          <input id="name" type="text" placeholder="Your name" autoComplete="name" value={full_name} onChange={(e) => setFull_name(e.target.value)} />

          <label htmlFor="email">Email</label>
          <input id="email" type="email" placeholder="you@example.com" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />

          <label htmlFor="password">Password</label>
          <input id="password" type="password" placeholder="••••••••" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />

          <button type="submit" className="btn-primary">
            Continue
          </button>
        </form>
        <p className="signup-login">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </main>
  )
}

export default SignUp
