import { useEffect, useState } from 'react'
import './TravelAgent.css'
import './SavedTrips.css'
import { getStoredUserId } from '../utils/authStorage'

function SavedTrips({ isLoggedIn }) {
  const [savedTrips, setSavedTrips] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [expandedTripId, setExpandedTripId] = useState(null)
  const [unsaveTripStatusById, setUnsaveTripStatusById] = useState({})
  const [purchaseTripStatusById, setPurchaseTripStatusById] = useState({})

  useEffect(() => {
    let ignore = false

    const loadSavedTrips = async () => {
      const userId = getStoredUserId()

      if (!userId) {
        if (!ignore) {
          setSavedTrips([])
          setExpandedTripId(null)
          setErrorMessage('Log in to view your saved trips.')
          setIsLoading(false)
        }
        return
      }

      if (!ignore) {
        setIsLoading(true)
        setErrorMessage('')
      }

      try {
        const userRes = await fetch(`http://127.0.0.1:5000/users/${encodeURIComponent(userId)}`)
        const userJson = await userRes.json()

        if (!userRes.ok || !userJson.success) {
          throw new Error(userJson.message || 'Failed to load user profile')
        }

        const savedTripIds = Array.isArray(userJson.user?.Saved_Trips_ID)
          ? userJson.user.Saved_Trips_ID.filter(
              (tripId) => typeof tripId === 'string' && tripId.trim() !== '',
            )
          : []

        if (savedTripIds.length === 0) {
          if (!ignore) {
            setSavedTrips([])
            setExpandedTripId(null)
          }
          return
        }

        const tripsRes = await fetch('http://127.0.0.1:5000/saved_trips', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tripIds: savedTripIds }),
        })
        const tripsJson = await tripsRes.json()

        if (!tripsRes.ok || !tripsJson.success) {
          throw new Error(tripsJson.message || 'Failed to load saved trips')
        }

        if (!ignore) {
          setSavedTrips(tripsJson.trips ?? [])
        }
      } catch (err) {
        console.error('Failed to load saved trips', err)
        if (!ignore) {
          setSavedTrips([])
          setExpandedTripId(null)
          setErrorMessage('Failed to load saved trips.')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    loadSavedTrips()

    return () => {
      ignore = true
    }
  }, [isLoggedIn])

  const getActivityImageUrl = (act) => {
    const first = Array.isArray(act?.pictures) ? act.pictures[0] : null
    if (typeof first === 'string' && first.trim().length > 0) return first
    const seed = encodeURIComponent(act?.id ?? act?.name ?? 'travel')
    return `https://picsum.photos/seed/${seed}/600/400`
  }

  const getTripKey = (trip) =>
    trip._id ?? `${trip.location ?? 'trip'}-${trip.trip_type ?? 'trip'}-${trip.season ?? 'season'}`

  const unsaveTrip = async (trip) => {
    const userId = getStoredUserId()
    const tripKey = getTripKey(trip)

    if (!userId || !trip._id) {
      setUnsaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
      return
    }

    setUnsaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'removing' }))

    try {
      const res = await fetch('http://127.0.0.1:5000/unsave_trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, tripId: trip._id }),
      })
      const json = await res.json()

      if (!res.ok || !json.success) {
        throw new Error(json.message || 'Failed to unsave trip')
      }

      setSavedTrips((curr) => curr.filter((savedTrip) => getTripKey(savedTrip) !== tripKey))
      setExpandedTripId((curr) => (curr === tripKey ? null : curr))
      setErrorMessage('')
    } catch (err) {
      console.error('Failed to unsave trip', err)
      setUnsaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
      setErrorMessage('Failed to remove this trip from your saved list.')
    }
  }

  const buyTrip = async (trip) => {
    const userId = getStoredUserId()
    const tripKey = getTripKey(trip)

    if (!userId) {
      setPurchaseTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
      return
    }

    setPurchaseTripStatusById((curr) => ({ ...curr, [tripKey]: 'saving' }))

    try {
      const res = await fetch('http://127.0.0.1:5000/buy_trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, trip }),
      })
      const json = await res.json()

      if (!res.ok || !json.success) {
        throw new Error(json.message || 'Failed to purchase trip')
      }

      setPurchaseTripStatusById((curr) => ({ ...curr, [tripKey]: 'saved' }))
      console.log(json.message || 'Trip purchased successfully', json.tripId ?? tripKey)
    } catch (err) {
      console.error('Failed to purchase trip', err)
      setPurchaseTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
    }
  }

  const getUnsaveTripLabel = (trip) => {
    const status = unsaveTripStatusById[getTripKey(trip)]
    if (status === 'removing') return 'Removing...'
    if (status === 'error') return 'Retry Remove'
    return 'Unsave Trip'
  }

  const getPurchaseTripLabel = (trip) => {
    const status = purchaseTripStatusById[getTripKey(trip)]
    if (status === 'saving') return 'Purchasing...'
    if (status === 'saved') return 'Trip Purchased'
    if (status === 'error') return 'Retry Purchase'
    return 'Purchase this trip'
  }

  return (
    <main className="saved-trips-page">
      <div className="section-inner">
        <header className="saved-trips-header">
          <h1>Saved Trips</h1>
          <p className="section-subtitle">
            Review the trips you saved and remove any you no longer want to keep.
          </p>
        </header>

        {errorMessage && (
          <div className="saved-trips-status saved-trips-status--error" role="status">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="saved-trips-status" role="status">
            Loading your saved trips...
          </div>
        ) : savedTrips.length === 0 ? (
          <div className="saved-trips-status">
            {isLoggedIn ? 'You have no saved trips yet.' : 'Log in to view your saved trips.'}
          </div>
        ) : (
          <section className="saved-trips-list" aria-label="Saved trips">
            {savedTrips.map((trip) => {
              const tripKey = getTripKey(trip)
              const isExpanded = expandedTripId === tripKey
              const unsaveStatus = unsaveTripStatusById[tripKey]
              const purchaseStatus = purchaseTripStatusById[tripKey]

              return (
                <div key={tripKey} className="trip-card">
                  <button
                    type="button"
                    className="trip-card__header trip-card__toggle"
                    onClick={() =>
                      setExpandedTripId((curr) =>
                        curr === tripKey ? null : tripKey,
                      )
                    }
                    aria-expanded={isExpanded}
                  >
                    <h3 className="trip-card__title">{trip.trip_type} Trip</h3>
                    <div className="trip-card__meta">
                      <span>
                        Trip price:{' '}
                        <strong>${trip.budget_usd ?? trip.activities_total_usd ?? 0}</strong>
                      </span>
                      <span className="trip-card__chevron" aria-hidden="true">
                        {isExpanded ? '▲' : '▼'}
                      </span>
                    </div>
                  </button>

                  <div className="trip-activity-grid">
                    {(trip.activities ?? []).slice(0, 3).map((act) => (
                      <div key={act.id} className="trip-activity-tile">
                        <img
                          className="trip-activity-tile__img"
                          src={getActivityImageUrl(act)}
                          alt={act.name ?? act.id ?? 'Activity'}
                          loading="lazy"
                        />
                        <div className="trip-activity-tile__text">
                          Before going to <strong>{act.name ?? act.id}</strong>
                        </div>
                      </div>
                    ))}
                  </div>

                  {isExpanded && (
                    <div className="trip-card__details">
                      <div className="trip-details-grid">
                        <div>
                          <div className="trip-detail-label">Location</div>
                          <div className="trip-detail-value">{trip.location ?? '—'}</div>
                        </div>
                        <div>
                          <div className="trip-detail-label">Season</div>
                          <div className="trip-detail-value">{trip.season ?? '—'}</div>
                        </div>
                        <div>
                          <div className="trip-detail-label">Total activities</div>
                          <div className="trip-detail-value">{(trip.activities ?? []).length}</div>
                        </div>
                        <div>
                          <div className="trip-detail-label">Total activity cost</div>
                          <div className="trip-detail-value">${trip.activities_total_usd ?? 0}</div>
                        </div>
                      </div>

                      <h4 className="trip-details-title">Experiences</h4>
                      <div className="trip-details-activities">
                        {(trip.activities ?? []).map((act) => (
                          <div key={act.id} className="trip-details-activity">
                            <img
                              className="trip-details-activity__img"
                              src={getActivityImageUrl(act)}
                              alt={act.name ?? act.id ?? 'Activity'}
                              loading="lazy"
                            />
                            <div className="trip-details-activity__info">
                              <div className="trip-details-activity__name">
                                {act.name ?? act.id}
                              </div>
                              <div className="trip-details-activity__price">
                                ${act.price_USD ?? 0}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="trip-card__actions">
                        <button
                          type="button"
                          className="unsave-trip-button"
                          disabled={unsaveStatus === 'removing'}
                          onClick={(e) => {
                            e.stopPropagation()
                            unsaveTrip(trip)
                          }}
                        >
                          {getUnsaveTripLabel(trip)}
                        </button>
                        <button
                          type="button"
                          className="purchase-button"
                          disabled={purchaseStatus === 'saving' || purchaseStatus === 'saved'}
                          onClick={(e) => {
                            e.stopPropagation()
                            buyTrip(trip)
                          }}
                        >
                          {getPurchaseTripLabel(trip)}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </section>
        )}
      </div>
    </main>
  )
}

export default SavedTrips
