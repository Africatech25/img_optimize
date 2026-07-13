import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import ParamsPanel from '../components/ParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'

import { track } from '@vercel/analytics'

const VIDEO_EXTENSIONS = new Set(['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp'])

function isVideoFile(filename) {
  const ext = filename.toLowerCase().split('.').pop()
  return VIDEO_EXTENSIONS.has(`.${ext}`)
}

export default function Optimizer() {
  const API_BASE = import.meta.env.VITE_API_URL || '';
  const [files, setFiles] = useState([])

  // Image params
  const [format, setFormat] = useState('webp')
  const [quality, setQuality] = useState(82)

  // Video params
  const [videoCodec, setVideoCodec] = useState('h264')
  const [videoQuality, setVideoQuality] = useState(28)
  const [resolution, setResolution] = useState('original')
  const [maxFps, setMaxFps] = useState('')

  // Common params
  const [prefix, setPrefix] = useState('')
  const [startNumber, setStartNumber] = useState(1)

  // UI state
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState([])
  const [result, setResult] = useState(null)

  // Config from API
  const [formats, setFormats] = useState({})
  const [videoCodecs, setVideoCodecs] = useState({})

  // Compute file types
  const hasImages = files.some(f => !isVideoFile(f.name))
  const hasVideos = files.some(f => isVideoFile(f.name))

  // Charger les formats disponibles au montage
  useEffect(() => {
    fetch(`${API_BASE}/api/formats`)
      .then(res => res.json())
      .then(data => {
        setFormats(data)
      })
      .catch(err => console.error('Erreur chargement formats:', err))

    fetch(`${API_BASE}/api/video/formats`)
      .then(res => res.json())
      .then(data => {
        setVideoCodecs(data)
      })
      .catch(err => console.error('Erreur chargement codecs vidéo:', err))
  }, [API_BASE])

  // Les qualités par défaut sont définies dans les useState initiaux

  const handleFilesAdded = (newFiles) => {
    setFiles(prev => [...prev, ...newFiles])
  }

  const handleRemoveFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleOptimize = async () => {
    if (files.length === 0 || !prefix.trim()) return

    setIsProcessing(true)
    setProgress([])
    setResult(null)

    // Préparer le FormData
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    formData.append('format', format)
    formData.append('quality', quality)
    formData.append('prefix', prefix)
    formData.append('start_number', startNumber)
    formData.append('codec', videoCodec)
    formData.append('video_quality', videoQuality)
    formData.append('resolution', resolution)
    if (maxFps) {
      formData.append('max_fps', maxFps)
    }

    try {
      // Démarrer l'optimisation
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Erreur lors du démarrage de l\'optimisation')
      }

      const data = await response.json()
      setJobId(data.job_id)

      // Écouter les événements SSE avec reconnexion automatique
      let retryCount = 0
      const MAX_RETRIES = 3
      const RETRY_DELAY = 2000

      const connectSSE = () => {
        const eventSource = new EventSource(`${API_BASE}/api/progress/${data.job_id}`)

        eventSource.onmessage = (event) => {
          const message = JSON.parse(event.data)

          if (message.type === 'done') {
            eventSource.close()
            retryCount = 0

            // Traquer l'événement de succès
            track('files_optimized', {
              images: data.total_images,
              videos: data.total_videos,
              format: format,
              codec: videoCodec,
            })

            // Récupérer les stats finales
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

          if (retryCount < MAX_RETRIES) {
            retryCount++
            console.log(`Reconnexion SSE tentative ${retryCount}/${MAX_RETRIES}...`)
            setTimeout(connectSSE, RETRY_DELAY * retryCount)
          } else {
            setIsProcessing(false)
          }
        }

        return eventSource
      }

      const sseRef = connectSSE()
      return () => sseRef.close()

    } catch (error) {
      console.error('Erreur:', error)
      alert(error.message || 'Une erreur est survenue lors de l\'optimisation')
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

  const handleDownload = () => {
    if (jobId) {
      window.location.href = `${API_BASE}/api/download/${jobId}`
    }
  }

  const canOptimize = files.length > 0 && prefix.trim() !== '' && !isProcessing

  return (
    <div className="min-h-screen pt-28">

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!result ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Params */}
            <div className="lg:col-span-1">
              <ParamsPanel
                format={format}
                setFormat={setFormat}
                quality={quality}
                setQuality={setQuality}
                formats={formats}
                videoCodec={videoCodec}
                setVideoCodec={setVideoCodec}
                videoQuality={videoQuality}
                setVideoQuality={setVideoQuality}
                videoCodecs={videoCodecs}
                resolution={resolution}
                setResolution={setResolution}
                maxFps={maxFps}
                setMaxFps={setMaxFps}
                prefix={prefix}
                setPrefix={setPrefix}
                startNumber={startNumber}
                setStartNumber={setStartNumber}
                canOptimize={canOptimize}
                onOptimize={handleOptimize}
                isProcessing={isProcessing}
                hasImages={hasImages}
                hasVideos={hasVideos}
              />
            </div>

            {/* Right Column - Files */}
            <div className="lg:col-span-2">
              {files.length === 0 ? (
                <DropZone onFilesAdded={handleFilesAdded} />
              ) : (
                <ImageGrid
                  files={files}
                  prefix={prefix}
                  format={format}
                  videoCodec={videoCodec}
                  startNumber={startNumber}
                  onRemoveFile={handleRemoveFile}
                  onFilesAdded={handleFilesAdded}
                />
              )}

              {/* Progress Log */}
              {isProcessing && (
                <div className="mt-8">
                  <ProgressLog progress={progress} totalImages={files.length} jobId={jobId} />
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Result View */
          <div className="max-w-4xl mx-auto">
            <ResultCard
              result={result}
              totalImages={files.length}
              onDownload={handleDownload}
              onReset={handleReset}
            />

            {/* Final Progress Log */}
            {progress.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-white mb-4">Détails du traitement</h3>
                <ProgressLog progress={progress} totalImages={files.length} jobId={jobId} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
