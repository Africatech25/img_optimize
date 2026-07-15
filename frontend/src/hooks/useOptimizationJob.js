import { useState, useRef, useEffect } from 'react'
import { track } from '@vercel/analytics'

const MAX_RETRIES = 3
const RETRY_DELAY = 2000

/**
 * Logique partagée entre les 4 vues d'action (optimiser images/vidéos,
 * signer, lisser) : upload, suivi SSE, téléchargement, reset.
 * `mode` est envoyé au backend et détermine l'action exécutée côté serveur.
 */
export default function useOptimizationJob({ mode, trackEventName }) {
  const API_BASE = import.meta.env.VITE_API_URL || ''
  const [files, setFiles] = useState([])
  const [prefix, setPrefix] = useState('')
  const [startNumber, setStartNumber] = useState(1)
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState([])
  const [result, setResult] = useState(null)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const handleFilesAdded = (newFiles) => {
    setFiles(prev => [...prev, ...newFiles])
  }

  const handleRemoveFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  // appendFields(formData) : le composant appelant ajoute ses champs spécifiques
  const handleProcess = async (appendFields) => {
    if (files.length === 0 || !prefix.trim()) return

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setIsProcessing(true)
    setProgress([])
    setResult(null)

    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('mode', mode)
    formData.append('prefix', prefix)
    formData.append('start_number', startNumber)
    if (appendFields) appendFields(formData)

    try {
      const response = await fetch(`${API_BASE}/api/optimize`, {
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
      alert(error.message || 'Une erreur est survenue')
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setFiles([])
    setPrefix('')
    setStartNumber(1)
    setProgress([])
    setResult(null)
    setJobId(null)
    setIsProcessing(false)
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
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      // Un blob: URL ne porte aucune information de nom/extension : sans
      // attribut `download` explicite, le fichier serait enregistré sans
      // extension. On récupère donc le vrai nom depuis Content-Disposition.
      const contentDisposition = res.headers.get('content-disposition') || ''
      const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/)
      a.download = filenameMatch
        ? filenameMatch[1]
        : `optimized-${jobId.slice(0, 8)}.zip`

      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Download error:', e)
      alert(e.message || 'Impossible de télécharger le fichier')
    }
  }

  const canProcess = files.length > 0 && prefix.trim() !== '' && !isProcessing

  return {
    API_BASE,
    files,
    prefix, setPrefix,
    startNumber, setStartNumber,
    isProcessing,
    jobId,
    progress,
    result,
    handleFilesAdded,
    handleRemoveFile,
    handleProcess,
    handleReset,
    handleDownload,
    canProcess,
  }
}
