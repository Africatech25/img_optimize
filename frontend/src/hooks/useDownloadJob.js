import { useState, useRef, useEffect } from 'react'
import { track } from '@vercel/analytics'

const MAX_RETRIES = 3
const RETRY_DELAY = 2000

/**
 * Logique de téléchargement vidéo par URL : appel à /api/download, suivi SSE,
 * téléchargement du résultat, reset. Réutilise le même mécanisme SSE que
 * useOptimizationJob.
 */
export default function useDownloadJob({ trackEventName }) {
  const API_BASE = import.meta.env.VITE_API_URL || ''
  const [url, setUrl] = useState('')
  const [cookies, setCookies] = useState('')
  const [optimize, setOptimize] = useState(true)
  const [prefix, setPrefix] = useState('')
  const [startNumber, setStartNumber] = useState(1)
  const [platforms, setPlatforms] = useState([])
  const [domains, setDomains] = useState([])
  const [downloadAvailable, setDownloadAvailable] = useState(true)
  const [maxSizeMb, setMaxSizeMb] = useState(500)
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState([])
  const [result, setResult] = useState(null)
  const [urlError, setUrlError] = useState('')
  const eventSourceRef = useRef(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/download/platforms`)
      .then(res => res.json())
      .then(data => {
        setPlatforms(data.platforms || [])
        setDomains(data.domains || [])
        setDownloadAvailable(data.available !== false)
        setMaxSizeMb(data.max_size_mb || 500)
      })
      .catch(err => console.error('Erreur chargement plateformes:', err))
  }, [API_BASE])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const canProcess = url.trim() !== '' && prefix.trim() !== '' && !isProcessing && downloadAvailable

  const validateClientSide = () => {
    const trimmed = url.trim()
    if (!/^https?:\/\//i.test(trimmed)) {
      setUrlError('URL invalide (http/https requis)')
      return false
    }
    try {
      const host = new URL(trimmed).hostname.toLowerCase()
      const isAllowed = domains.length === 0 || domains.some(d => host === d || host.endsWith('.' + d))
      if (!isAllowed) {
        setUrlError('Plateforme non supportée')
        return false
      }
    } catch {
      setUrlError('URL invalide')
      return false
    }
    setUrlError('')
    return true
  }

  const handleProcess = async (appendFields) => {
    if (!url.trim() || !prefix.trim() || !downloadAvailable) return
    if (!validateClientSide()) return

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setIsProcessing(true)
    setProgress([])
    setResult(null)

    const formData = new FormData()
    formData.append('url', url.trim())
    formData.append('prefix', prefix)
    formData.append('start_number', startNumber)
    if (appendFields) appendFields(formData)

    try {
      const response = await fetch(`${API_BASE}/api/download`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Erreur lors du démarrage')
      }

      const data = await response.json()
      setJobId(data.job_id)

      let retryCount = 0

      const connectSSE = () => {
        const eventSource = new EventSource(`${API_BASE}/api/progress/${data.job_id}`)
        eventSourceRef.current = eventSource

        eventSource.onmessage = (event) => {
          const message = JSON.parse(event.data)

          if (message.type === 'done') {
            eventSource.close()
            eventSourceRef.current = null
            retryCount = 0

            if (trackEventName) {
              track(trackEventName, { count: data.total_files })
            }

            fetch(`${API_BASE}/api/job/${data.job_id}`)
              .then(res => res.json())
              .then(jobData => {
                setResult(jobData)
                setIsProcessing(false)
              })
          } else {
            retryCount = 0
            setProgress(prev => [...prev, message])
          }
        }

        eventSource.onerror = (error) => {
          console.error('Erreur SSE:', error)
          eventSource.close()
          eventSourceRef.current = null

          if (retryCount < MAX_RETRIES) {
            retryCount++
            setTimeout(connectSSE, RETRY_DELAY * retryCount)
          } else {
            setIsProcessing(false)
          }
        }
      }

      connectSSE()
    } catch (error) {
      console.error('Erreur:', error)
      setUrlError(error.message || 'Une erreur est survenue')
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setUrl('')
    setCookies('')
    setOptimize(true)
    setPrefix('')
    setStartNumber(1)
    setProgress([])
    setResult(null)
    setJobId(null)
    setIsProcessing(false)
    setUrlError('')
  }

  const handleDownload = async () => {
    if (!jobId) return
    try {
      const res = await fetch(`${API_BASE}/api/download/${jobId}`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur de téléchargement')
      }
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl

      const contentDisposition = res.headers.get('content-disposition') || ''
      const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/)
      a.download = filenameMatch
        ? filenameMatch[1]
        : `optimized-${jobId.slice(0, 8)}.zip`

      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(blobUrl)
    } catch (e) {
      console.error('Download error:', e)
      alert(e.message || 'Impossible de télécharger le fichier')
    }
  }

  return {
    API_BASE,
    url, setUrl,
    cookies, setCookies,
    optimize, setOptimize,
    prefix, setPrefix,
    startNumber, setStartNumber,
    platforms, downloadAvailable, maxSizeMb,
    isProcessing,
    jobId,
    progress,
    result,
    urlError, setUrlError,
    canProcess,
    handleProcess,
    handleReset,
    handleDownload,
  }
}
