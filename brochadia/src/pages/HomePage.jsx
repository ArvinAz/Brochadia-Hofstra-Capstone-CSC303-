function HomePage() {
  const itineraryDays = [
    { day: 1, title: 'Arrival & Old Town', activities: ['Land at airport', 'Check into hotel', 'Evening stroll through historic district', 'Dinner at local bistro'] },
    { day: 2, title: 'Museums & Markets', activities: ['Morning visit to City Museum', 'Lunch at central market', 'Afternoon art gallery', 'Sunset at viewpoint'] },
    { day: 3, title: 'Day Trip', activities: ['Full-day excursion to nearby village', 'Local cuisine tasting', 'Return by evening'] },
    { day: 4, title: 'Departure', activities: ['Breakfast at café', 'Final souvenir shopping', 'Transfer to airport'] }
  ]

  const destinations = [
    { name: 'Historic Center', description: 'Wander through cobblestone streets and ancient architecture.', icon: '🏛️' },
    { name: 'Local Markets', description: 'Taste fresh produce and artisanal goods.', icon: '🛒' },
    { name: 'Scenic Viewpoints', description: 'Panoramic views of the city and beyond.', icon: '🌅' }
  ]

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <h1>Your Journey,<br />Mapped Out</h1>
          <p>Plan your perfect trip with our simple, beautiful itineraries. No hassle—just the places you want to see.</p>
          <button type="button" className="btn-primary">Start Planning</button>
        </div>
        <div className="hero-decoration" aria-hidden="true" />
      </section>

      <section id="itinerary" className="section itinerary-section">
        <div className="section-inner">
          <h2>Sample Itinerary</h2>
          <p className="section-subtitle">A 4-day example to inspire your next adventure</p>
          <div className="itinerary-days">
            {itineraryDays.map((item) => (
              <article key={item.day} className="itinerary-card">
                <div className="itinerary-day-badge">Day {item.day}</div>
                <h3>{item.title}</h3>
                <ul>
                  {item.activities.map((activity, i) => (
                    <li key={i}>{activity}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="destinations" className="section destinations-section">
        <div className="section-inner">
          <h2>Explore</h2>
          <p className="section-subtitle">Highlights from your trip</p>
          <div className="destinations-grid">
            {destinations.map((d) => (
              <div key={d.name} className="destination-card">
                <span className="destination-icon">{d.icon}</span>
                <h3>{d.name}</h3>
                <p>{d.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}

export default HomePage
