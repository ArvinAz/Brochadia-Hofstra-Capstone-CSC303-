import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import './ReviewTrip.css'
import { getStoredUserId } from '../utils/authStorage'

function ReviewTrip() {
  const navigate = useNavigate()
  const location = useLocation()
  const { tripId } = useParams()
  const fallbackTrip = location.state?.trip ?? null
  const [tripDetails, setTripDetails] = useState(fallbackTrip)
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    let ignore = false

    const loadPurchasedTrip = async () => {
      const userId = getStoredUserId()

      if (!tripId) {
        if (!ignore) {
          setErrorMessage('Missing trip id for this review.')
          setIsLoading(false)
        }
        return
      }

      if (!userId) {
        if (!ignore) {
          setErrorMessage('Log in to review a purchased trip.')
          setIsLoading(false)
        }
        return
      }

      if (!ignore) {
        setIsLoading(true)
        setErrorMessage('')
      }

      try {
        const res = await fetch(`http://127.0.0.1:5000/users/${encodeURIComponent(userId)}`)
        const json = await res.json()

        if (!res.ok || !json.success) {
          throw new Error(json.message || 'Failed to load user profile')
        }

        const purchasedTrip = Array.isArray(json.user?.trip_history)
          ? json.user.trip_history.find(
              (trip) => String(trip?.trip_id ?? '').trim() === String(tripId).trim(),
            )
          : null

        if (!ignore) {
          if (purchasedTrip) {
            setTripDetails((curr) => ({ ...(curr ?? {}), ...purchasedTrip }))
            setRating(Number(purchasedTrip.review_rating) || 0)
            setDescription(purchasedTrip.review_description ?? '')
          } else if (!fallbackTrip) {
            setErrorMessage('We could not find this trip in your purchase history.')
          }
        }
      } catch (err) {
        console.error('Failed to load purchased trip', err)
        if (!ignore) {
          setErrorMessage('Failed to load this purchased trip.')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    loadPurchasedTrip()

    return () => {
      ignore = true
    }
  }, [fallbackTrip, tripId])

  const activeStars = hoveredRating || rating

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    const userId = getStoredUserId()

    if (!userId) {
      setErrorMessage('Log in to submit a review.')
      return
    }

    if (!tripId) {
      setErrorMessage('Missing trip id for this review.')
      return
    }

    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      setErrorMessage('Choose a star rating from 1 to 5.')
      return
    }

    if (description.trim() === '') {
      setErrorMessage('Add a short description before submitting your review.')
      return
    }

    setIsSubmitting(true)

    try {
      const res = await fetch('http://127.0.0.1:5000/review_trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          trip_id: tripId,
          description: description.trim(),
          rating,
        }),
      })
      const json = await res.json()

      if (!res.ok || !json.success) {
        throw new Error(json.message || 'Failed to save trip review')
      }

      setSuccessMessage(json.message || 'Trip review saved successfully.')
      setTripDetails((curr) => ({
        ...(curr ?? {}),
        review_rating: rating,
        review_description: description.trim(),
      }))
    } catch (err) {
      console.error('Failed to save trip review', err)
      setErrorMessage(err.message || 'Failed to save trip review.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="review-trip-page">
      <div className="section-inner">
        <div className="review-trip-shell">
          <div className="review-trip-panel">
            <p className="review-trip-eyebrow">Purchased Trip Review</p>
            <h1>Rate how your trip went</h1>
            <p className="review-trip-subtitle">
              Leave a 1 to 5 star rating and a short description so your future trip
              recommendations can adapt to what you enjoyed.
            </p>

            {tripDetails && (
              <section className="review-trip-summary" aria-label="Trip summary">
                <div>
                  <span className="review-trip-summary__label">Location</span>
                  <strong>{tripDetails.location ?? 'Unknown location'}</strong>
                </div>
                <div>
                  <span className="review-trip-summary__label">Trip type</span>
                  <strong>{tripDetails.trip_type ?? 'Trip'}</strong>
                </div>
                <div>
                  <span className="review-trip-summary__label">Budget</span>
                  <strong>${tripDetails.budget_usd ?? tripDetails.activities_total_usd ?? 0}</strong>
                </div>
              </section>
            )}

            {errorMessage && (
              <div className="review-trip-status review-trip-status--error" role="status">
                {errorMessage}
              </div>
            )}

            {successMessage && (
              <div className="review-trip-status review-trip-status--success" role="status">
                {successMessage}
              </div>
            )}

            {isLoading ? (
              <div className="review-trip-status" role="status">
                Loading your purchased trip...
              </div>
            ) : (
              <form className="review-trip-form" onSubmit={handleSubmit}>
                <div className="review-trip-stars" aria-label="Choose a star rating">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      className={`review-trip-star ${activeStars >= star ? 'review-trip-star--active' : ''}`}
                      aria-label={`Rate ${star} out of 5 stars`}
                      aria-pressed={rating === star}
                      onClick={() => setRating(star)}
                      onMouseEnter={() => setHoveredRating(star)}
                      onMouseLeave={() => setHoveredRating(0)}
                    >
                      ★
                    </button>
                  ))}
                </div>

                <label className="review-trip-field" htmlFor="trip-review-description">
                  <span>How was it?</span>
                  <textarea
                    id="trip-review-description"
                    rows="6"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Tell us what you liked or disliked about this trip."
                  />
                </label>

                <div className="review-trip-actions">
                  <button type="submit" className="btn-primary" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving review...' : 'Save review'}
                  </button>
                  <button
                    type="button"
                    className="review-trip-secondary"
                    onClick={() => navigate('/travel-agent')}
                  >
                    Back to Travel Agent
                  </button>
                </div>
              </form>
            )}

            <p className="review-trip-footer">
              Want to review saved destinations too? <Link to="/saved-trips">Open saved trips</Link>.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}

export default ReviewTrip
