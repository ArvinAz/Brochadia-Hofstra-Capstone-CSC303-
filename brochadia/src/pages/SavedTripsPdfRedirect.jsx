import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function SavedTripsPdfRedirect() {
  const navigate = useNavigate()

  useEffect(() => {
    navigate('/your_pdf', { replace: true })
  }, [navigate])

  return (
    <main className="saved-trips-page">
      <div className="section-inner">
        <div className="saved-trips-status" role="status">
          Redirecting to your PDF...
        </div>
      </div>
    </main>
  )
}

export default SavedTripsPdfRedirect
