import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import ParamsPanel from '../components/ParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'

export default function Optimizer() {
  const API_BASE = import.meta.env.VITE_API_URL || '';
  const [files, setFiles] = useState([])
  const [format, setFormat] = useState('webp')
  const [quality, setQuality] = useState(82)
  const [prefix, setPrefix] = useState('')
  const [startNumber, setStartNumber] = useState(1)
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState([])
  const [result, setResult] = useState(null)
  const [formats, setFormats] = useState({})

  // Charger les formats disponibles au montage
  useEffect(() => {
    fetch(`${API_BASE}/api/formats`)
      .then(res => res.json())
      .then(data => {
        setFormats(data)
        // Définir la qualité par défaut selon le format
        if (data[format]) {
          setQuality(data[format].default_quality)
        }
      })
      .catch(err => console.error('Erreur chargement formats:', err))
  }, [])

  // Mettre à jour la qualité par défaut quand le format change
  useEffect(() => {
    if (formats[format]) {
      setQuality(formats[format].default_quality)
    }
  }, [format, formats])

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

    try {
      // Démarrer l'optimisation
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Erreur lors du démarrage de l\'optimisation')
      }

      const data = await response.json()
      setJobId(data.job_id)

      // Écouter les événements SSE
      const eventSource = new EventSource(`${API_BASE}/api/progress/${data.job_id}`)

      eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data)

        if (message.type === 'done') {
          eventSource.close()
          // Récupérer les stats finales
          fetch(`${API_BASE}/api/job/${data.job_id}`)
            .then(res => res.json())
            .then(jobData => {
              setResult(jobData)
              setIsProcessing(false)
            })
        } else {
          setProgress(prev => [...prev, message])
        }
      }

      eventSource.onerror = (error) => {
        console.error('Erreur SSE:', error)
        eventSource.close()
        setIsProcessing(false)
      }

    } catch (error) {
      console.error('Erreur:', error)
      alert('Une erreur est survenue lors de l\'optimisation')
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
                prefix={prefix}
                setPrefix={setPrefix}
                format={format}
                setFormat={setFormat}
                quality={quality}
                setQuality={setQuality}
                startNumber={startNumber}
                setStartNumber={setStartNumber}
                formats={formats}
                canOptimize={canOptimize}
                onOptimize={handleOptimize}
                isProcessing={isProcessing}
              />
            </div>

            {/* Right Column - Images */}
            <div className="lg:col-span-2">
              {files.length === 0 ? (
                <DropZone onFilesAdded={handleFilesAdded} />
              ) : (
                <ImageGrid
                  files={files}
                  prefix={prefix}
                  format={format}
                  startNumber={startNumber}
                  onRemoveFile={handleRemoveFile}
                  onFilesAdded={handleFilesAdded}
                />
              )}

              {/* Progress Log */}
              {isProcessing && progress.length > 0 && (
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
