import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import HomePage from './pages/HomePage'
import SignUp from './pages/SignUp'
import Login from './pages/Login'
import TravelAgent from './pages/TravelAgent'
import Questionnaire from './pages/Questionnaire'
import './App.css'
import { clearStoredUserId, getStoredUserId } from './utils/authStorage'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => Boolean(getStoredUserId()))
  const navigate = useNavigate()

  const handleLogout = () => {
    clearStoredUserId()
    setIsLoggedIn(false)
    navigate('/')
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <Link to="/" className="logo">Brochadia</Link>
          <nav className="nav">
            <a href="/#itinerary">Itinerary</a>
            <a href="/#destinations">Destinations</a>
            <Link to="/travel-agent">Travel Agent</Link>
            <a href="/#contact">Contact</a>
            {isLoggedIn ? (
              <>
                <button type="button" className="nav-link-button" onClick={handleLogout}>
                  Log off
                </button>
                <Link to="/saved-trips">Saved Trips</Link>
              </>
            ) : (
              <>
                <Link to="/login">Log in</Link>
                <Link to="/signup">Sign up</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login onLoginSuccess={() => setIsLoggedIn(true)} />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/signup/questionnaire" element={<Questionnaire onSignupSuccess={() => setIsLoggedIn(true)} />} />
        <Route path="/travel-agent" element={<TravelAgent isLoggedIn={isLoggedIn} />} />
        
      </Routes>

      <footer id="contact" className="footer">
        <div className="footer-inner">
          <p className="footer-brand">Brochadia</p>
          <p className="footer-tagline">Your travel itinerary, simplified.</p>
          <div className="footer-links">
            <a href="#">About</a>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </div>
          <p className="footer-copy">© 2025 Brochadia. Front-end template only.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
