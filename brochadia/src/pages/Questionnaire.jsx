import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import './Questionnaire.css'
import { storeUserId } from '../utils/authStorage'
import {
  clearSignupDraft,
  getSignupDraft,
  storeSignupDraft,
} from '../utils/signupDraftStorage'

const TRIP_TYPES = ['Leisure', 'Cultural', 'Honeymoon', 'Adventure', 'Business']

const CONTINENTS = [
  'Africa',
  'Asia',
  'Europe',
  'North America',
  'South America',
  'Oceania',
  'Antarctica',
]

function Questionnaire({ onSignupSuccess }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [signupDraft, setSignupDraft] = useState(() => location.state ?? getSignupDraft())
  const [preferredTrip, setPreferredTrip] = useState('Leisure')
  const [tripContinent, setTripContinent] = useState('')
  const [tripCountry, setTripCountry] = useState('')
  const [travelPartySize, setTravelPartySize] = useState('1')
  const [tripDate, setTripDate] = useState('')
  const [tripBudget, setTripBudget] = useState('')
  const [tripDetails, setTripDetails] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (location.state) {
      setSignupDraft(location.state)
      storeSignupDraft(location.state)
    }
  }, [location.state])

  useEffect(() => {
    if (!signupDraft) {
      navigate('/signup', { replace: true })
    }
  }, [navigate, signupDraft])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!signupDraft) {
      setError('Your signup session expired. Please start again.')
      navigate('/signup', { replace: true })
      return
    }

    if (!tripContinent || !tripCountry.trim() || !travelPartySize || !tripDate || !tripBudget) {
      setError('Complete all required questionnaire fields before continuing')
      return
    }

    setLoading(true)

    try {
      const res = await fetch('http://127.0.0.1:5000/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...signupDraft,
          preferred_trip: preferredTrip,
          trip_continent: tripContinent,
          trip_country: tripCountry.trim(),
          travel_party_size: travelPartySize,
          trip_date: tripDate,
          trip_budget: tripBudget,
          trip_details: tripDetails.trim(),
        }),
      })

      const json = await res.json()
      if (!res.ok || !json.success) {
        setError(json.message || 'Failed to complete signup')
        return
      }

      if (!json.userId) {
        setError('Failed to complete signup: missing user id')
        return
      }

      clearSignupDraft()
      storeUserId(json.userId)
      if (onSignupSuccess) onSignupSuccess()
      navigate('/')
    } catch (err) {
      setError('Network error while completing signup')
    } finally {
      setLoading(false)
    }
  }

  if (!signupDraft) return null

  return (
    <main className="questionnaire-page">
      <div className="questionnaire-shell">
        <div className="questionnaire-header">
          <p className="questionnaire-step">Step 2 of 2</p>
          <h1>Tell us how you travel</h1>
          <p className="questionnaire-subtitle">
            Pick your preferred trip style and share one trip you&apos;ve already taken.
          </p>
        </div>

        <div className="questionnaire-summary">
          <div>
            <span className="questionnaire-summary-label">Signing up as</span>
            <strong>{signupDraft.full_name}</strong>
          </div>
          <div>
            <span className="questionnaire-summary-label">Email</span>
            <strong>{signupDraft.email}</strong>
          </div>
        </div>

        {error && <p className="questionnaire-error">{error}</p>}

        <form className="questionnaire-form" onSubmit={handleSubmit}>
          <section className="questionnaire-section">
            <div className="questionnaire-section-copy">
              <h2>Preferred Trip</h2>
              <p>Select the travel style you usually enjoy most.</p>
            </div>

            <div className="questionnaire-option-grid">
              {TRIP_TYPES.map((tripType) => (
                <label
                  key={tripType}
                  className={`questionnaire-option ${preferredTrip === tripType ? 'questionnaire-option--selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="preferred_trip"
                    value={tripType}
                    checked={preferredTrip === tripType}
                    onChange={() => setPreferredTrip(tripType)}
                  />
                  <span>{tripType}</span>
                </label>
              ))}
            </div>
          </section>

          <section className="questionnaire-section">
            <div className="questionnaire-section-copy">
              <h2>Previous Trip</h2>
              <p>Share one trip so your future recommendations can be more personal.</p>
            </div>

            <div className="questionnaire-grid">
              <label className="questionnaire-field">
                <span>Continent</span>
                <select value={tripContinent} onChange={(e) => setTripContinent(e.target.value)}>
                  <option value="">Choose a continent</option>
                  {CONTINENTS.map((continent) => (
                    <option key={continent} value={continent}>
                      {continent}
                    </option>
                  ))}
                </select>
              </label>

              <label className="questionnaire-field">
                <span>Country</span>
                <input
                  type="text"
                  placeholder="Japan"
                  value={tripCountry}
                  onChange={(e) => setTripCountry(e.target.value)}
                />
              </label>

              <label className="questionnaire-field">
                <span>How many people went?</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={travelPartySize}
                  onChange={(e) => setTravelPartySize(e.target.value)}
                />
              </label>

              <label className="questionnaire-field">
                <span>When was it?</span>
                <input
                  type="date"
                  value={tripDate}
                  onChange={(e) => setTripDate(e.target.value)}
                />
              </label>

              <label className="questionnaire-field questionnaire-field--full">
                <span>Budget for the trip (USD)</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="2500"
                  value={tripBudget}
                  onChange={(e) => setTripBudget(e.target.value)}
                />
              </label>

              <label className="questionnaire-field questionnaire-field--full">
                <span>What did you do there? (Optional)</span>
                <textarea
                  rows="5"
                  placeholder="Share the highlights, activities, pace of the trip, and anything else you loved."
                  value={tripDetails}
                  onChange={(e) => setTripDetails(e.target.value)}
                />
              </label>
            </div>
          </section>

          <div className="questionnaire-actions">
            <button type="button" className="questionnaire-back" onClick={() => navigate('/signup')}>
              Back
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Creating account...' : 'Finish Sign Up'}
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}

export default Questionnaire
