import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './your_pdf.css'
import { getStoredUserId } from '../utils/authStorage'

function PdfDisplayPage() {
  const location = useLocation()
  const userIdFromState =
    typeof location.state === 'string' ? location.state : location.state?.userId
  const userId = userIdFromState ?? getStoredUserId()

  const [pdfUrl, setPdfUrl] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!userId) {
      setError('No user ID was found for this PDF. Complete signup again and retry.')
      setIsLoading(false)
      return undefined
    }

    let objectUrl = ''
    let ignore = false

    const loadPdf = async () => {
      setIsLoading(true)
      setError('')

      try {
        const response = await fetch(`http://127.0.0.1:5000/download/${encodeURIComponent(userId)}`)

        if (!response.ok) {
          console.log(response)
          throw new Error('Failed to fetch the PDF document.')
          
        }

        const blob = await response.blob()
        objectUrl = window.URL.createObjectURL(blob)

        if (!ignore) {
          setPdfUrl(objectUrl)
        }
      } catch (err) {
        console.error('Error fetching PDF:', err)
        if (!ignore) {
          setPdfUrl('')
          setError('Could not load the PDF document from the server.')
        }
      } finally {
        if (!ignore) {
          setIsLoading(false)
        }
      }
    }

    loadPdf()

    return () => {
      ignore = true
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl)
      }
    }
  }, [userId])

  return (
    <main className="pdf-page">
      <div className="pdf-page__shell">
        <header className="pdf-page__header">
          <p className="pdf-page__eyebrow">Signup Complete</p>
          <h1>Your PDF Document</h1>
          <p className="pdf-page__subtitle">
            Review the PDF generated for your account below.
          </p>
        </header>

        {error ? (
          <div className="pdf-page__status pdf-page__status--error" role="status">
            {error}
          </div>
        ) : isLoading ? (
          <div className="pdf-page__status" role="status">
            Loading document from server...
          </div>
        ) : (
          <div className="pdf-page__viewer">
            <iframe
              src={pdfUrl}
              title="User PDF Viewer"
              className="pdf-page__frame"
            />
          </div>
        )}
      </div>
    </main>
  )
}

export default PdfDisplayPage
