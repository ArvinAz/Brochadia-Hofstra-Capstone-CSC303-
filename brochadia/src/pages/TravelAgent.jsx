import { useEffect, useState } from 'react'
import './TravelAgent.css'
import { getStoredUserId } from '../utils/authStorage'

const DEFAULT_TRIP_PREF = 'Leisure'

const CONTINENTS = [
  'Africa',
  'Asia',
  'Europe',
  'North America',
  'South America',
  'Oceania',
  'Antarctica',
].map((label) => ({
  id: label.toLowerCase().replace(/\s+/g, '-'),
  label,
}))

function TravelAgent({ isLoggedIn }) {
  const [trip_pref, setTripPref] = useState(DEFAULT_TRIP_PREF)
  const [selected, setSelected] = useState(null)
  const [countriesForSelected, setCountriesForSelected] = useState([])
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [tripsForCountry, setTripsForCountry] = useState([])
  const [expandedTripId, setExpandedTripId] = useState(null)
  const [saveTripStatusById, setSaveTripStatusById] = useState({})

  useEffect(() => {
    const userId = getStoredUserId()

    if (!userId) {
      setTripPref(DEFAULT_TRIP_PREF)
      return
    }

    const loadPreferredTrip = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5000/users/${encodeURIComponent(userId)}`)
        const json = await res.json()

        if (!res.ok || !json.success) {
          console.error('Failed to load preferred trip', json.message)
          setTripPref(DEFAULT_TRIP_PREF)
          return
        }

        const preferredTrip = json.user?.preferred_trip
        setTripPref(preferredTrip || DEFAULT_TRIP_PREF)
        console.log('Loaded preferred_trip for user:', userId, preferredTrip || DEFAULT_TRIP_PREF)
      } catch (err) {
        console.error('Failed to fetch user preference', err)
        setTripPref(DEFAULT_TRIP_PREF)
      }
    }

    loadPreferredTrip()
  }, [isLoggedIn])

  const getActivityImageUrl = (act) => {
    const first = Array.isArray(act?.pictures) ? act.pictures[0] : null
    if (typeof first === 'string' && first.trim().length > 0) return first
    const seed = encodeURIComponent(act?.id ?? act?.name ?? 'travel')
    return `https://picsum.photos/seed/${seed}/600/400`
  }

  const getTripKey = (trip) =>
    trip._id ?? `${trip.location ?? 'trip'}-${trip.trip_type ?? 'trip'}-${trip.season ?? 'season'}`

  const getCountries = async (continentLabel) => {
    setSelected(continentLabel)
    setSelectedCountry(null)
    setTripsForCountry([])
    setExpandedTripId(null)

    try {
      const res = await fetch(`http://127.0.0.1:5000/countries?continent=${encodeURIComponent(continentLabel)}`)
      const json = await res.json()
      // Expecting { success: true, continent: "...", countries: [...] }
      setCountriesForSelected(json.countries ?? [])
    } catch (err) {
      console.error('Failed to load countries', err)
      setCountriesForSelected([])
      setTripsForCountry([])
    }
  }

  const getTrips = async (country) => {
    setSelectedCountry(country)
    setExpandedTripId(null)
    try {
      const userId = getStoredUserId()
      const params = new URLSearchParams({
        trip_type: trip_pref,
        Country: country,
      })

      if (userId) {
        params.set('userId', userId)
      }

      const res = await fetch(`http://127.0.0.1:5000/trip?${params.toString()}`)
      const json = await res.json()
      console.log('Trips response for', country, json)
      setTripsForCountry(json.trips ?? [])
    } catch (err) {
      console.error('Failed to load trips', err)
      setTripsForCountry([])
    }
  }

  const saveTrip = async (trip) => {
    const userId = getStoredUserId()
    const tripKey = getTripKey(trip)

    if (!userId) {
      console.error('Cannot save trip without a logged-in user')
      setSaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
      return
    }

    setSaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'saving' }))

    try {
      const res = await fetch('http://127.0.0.1:5000/save_trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, trip }),
      })
      const json = await res.json()

      if (!res.ok || !json.success) {
        throw new Error(json.message || 'Failed to save trip')
      }

      setSaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'saved' }))
      console.log(json.message || 'Trip saved successfully', json.tripId ?? tripKey)
    } catch (err) {
      console.error('Failed to save trip', err)
      setSaveTripStatusById((curr) => ({ ...curr, [tripKey]: 'error' }))
    }
  }

  const getSaveTripLabel = (trip) => {
    const status = saveTripStatusById[getTripKey(trip)]
    if (status === 'saving') return 'Saving...'
    if (status === 'saved') return 'Trip Saved'
    if (status === 'error') return 'Retry Save'
    return 'Save Trip'
  }

  //const getTrips = async

  return (
    <main className="travel-agent-page">
      <div className="section-inner">
        <header className="travel-agent-header">
          <h1>Travel Agent</h1>
          <p className="section-subtitle">
            Tap a continent to explore where your next adventure could take you.
          </p>
        </header>
        

        <section className="continent-map" aria-label="World continents map">
          {CONTINENTS.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`continent-chip ${selected === c.label ? 'continent-chip--active' : ''}`}
              onClick={() => getCountries(c.label)}
            >
              {c.label}
            </button>
          ))}
        </section>

        <section className="continent-selection" aria-live="polite">
          {selected ? (
            <>
              <p className="selection-message">
                You&apos;ve chosen{' '}
                <span className="selection-highlight">{selected}</span> as your travel continent.
              </p>
              <div className="country-list">
                <h2>Popular countries in {selected}</h2>
                <div className="country-chips">
                  {countriesForSelected.map((country) => (
                    <button
                      key={country}
                      type="button"
                      className="country-chip"
                      onClick={() => getTrips(country)}
                    >
                      {country}
                    </button>
                  ))}
                </div>
              </div>

              {selectedCountry && (
                <div className="country-list">
                  <h2>Experiences in {selectedCountry}</h2>
                  {tripsForCountry.length === 0 ? (
                    <p className="selection-message selection-message--muted">
                      No trips found yet for this country.
                    </p>
                  ) : (
                    <div>
                      {tripsForCountry.map((trip) => {
                        const tripKey = getTripKey(trip)
                        const isExpanded = expandedTripId === tripKey
                        const saveStatus = saveTripStatusById[tripKey]

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
                                  <strong>
                                    ${trip.budget_usd ?? trip.activities_total_usd ?? 0}
                                  </strong>
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
                                    <div className="trip-detail-value">
                                      {trip.location ?? selectedCountry}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="trip-detail-label">Season</div>
                                    <div className="trip-detail-value">
                                      {trip.season ?? '—'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="trip-detail-label">Total activities</div>
                                    <div className="trip-detail-value">
                                      {(trip.activities ?? []).length}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="trip-detail-label">Total activity cost</div>
                                    <div className="trip-detail-value">
                                      ${trip.activities_total_usd ?? 0}
                                    </div>
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
                                  {isLoggedIn && (
                                    <button
                                      type="button"
                                      className="save-trip-button"
                                      disabled={saveStatus === 'saving' || saveStatus === 'saved'}
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        saveTrip(trip)
                                      }}
                                    >
                                      {getSaveTripLabel(trip)}
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    className="purchase-button"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      console.log('Purchase trip', trip._id)
                                    }}
                                  >
                                    Purchase this trip
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="selection-message selection-message--muted">
              Select a continent above to see your choice and a list of countries you can travel to.
            </p>
          )}
        </section>
      </div>
    </main>
  )
}

export default TravelAgent
