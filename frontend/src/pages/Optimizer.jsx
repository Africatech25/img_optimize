import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import ParamsPanel from '../components/ParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'
import PDFRepair from '../components/PDFRepair'

import { track } from '@vercel/analytics'

export default function Optimizer() {
  const API_BASE = import.meta.env.VITE_API_URL || '';
  const [activeTab, setActiveTab] = useState('images') // 'images' ou 'pdf'
  const [files, setFiles] = useState([])
  const [format, setFormat] = useState('webp')
  const [quality, setQuality] = useState(82)
  const [prefix, setPrefix] = useState('')
  const [startNumber, setStartNumber] = useState(1)
  const [smoothing, setSmoothing] = useState(0)
  const [watermark, setWatermark] = useState({
    enabled: false,
    type: 'text',
    text: '',
    logo: null,
    position: 'bottom-right',
    opacity: 50
  })
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

  const handleProcess = async (type = 'both') => {
    // Pour le lissage uniquement, on n'a pas forcément besoin du préfixe SEO
    const isSmoothingOnly = type === 'smoothing'
    if (files.length === 0 || (!isSmoothingOnly && !prefix.trim())) return

    setIsProcessing(true)
    setProgress([])
    setResult(null)

    // Préparer le FormData
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    // Si type 'smoothing', on utilise le nom d'origine ou un préfixe par défaut si vide
    const finalPrefix = isSmoothingOnly && !prefix.trim() ? 'smoothed' : prefix

    let finalQuality = quality;
    if (type === 'smoothing') finalQuality = 95;
    if (type === 'signature_only') finalQuality = 100;

    formData.append('format', format)
    formData.append('quality', finalQuality) 
    formData.append('prefix', finalPrefix)
    formData.append('start_number', startNumber)
    formData.append('smoothing', (type === 'general' || type === 'watermark' || type === 'signature_only') ? 0 : smoothing)

    // Paramètres de Watermark
    if (watermark.enabled) {
      formData.append('watermark_enabled', 'true')
      formData.append('watermark_type', watermark.type)
      formData.append('watermark_text', watermark.text)
      formData.append('watermark_position', watermark.position)
      formData.append('watermark_opacity', watermark.opacity)
      
      if (watermark.type === 'image' && watermark.logo) {
        formData.append('watermark_logo', watermark.logo)
      }
    }

    try {
      // Démarrer l'optimisation
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.detail || `Erreur ${response.status}: ${response.statusText}`
        console.error('[API Error]', errorMsg)
        throw new Error(errorMsg)
      }

      const data = await response.json()
      setJobId(data.job_id)

      // Écouter les événements SSE
      const eventSource = new EventSource(`${API_BASE}/api/progress/${data.job_id}`)

      eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data)

        if (message.type === 'done') {
          eventSource.close()
          
          // Traquer l'événement de succès
          track('images_optimized', { 
            count: files.length, 
            format: format,
            quality: quality 
          })

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
      alert(`Une erreur est survenue lors de l'optimisation :\n${error.message}`)
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setFiles([])
    setPrefix('')
    setSmoothing(0)
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
  const canSmooth = files.length > 0 && !isProcessing && smoothing > 0

  return (
    <div className="min-h-screen pt-28">

      {/* Tab Navigation */}
      <div className="sticky top-20 z-40 bg-slate-950/80 backdrop-blur-lg border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-0">
            <button
              onClick={() => setActiveTab('images')}
              className={`px-6 py-4 font-semibold transition-all duration-300 border-b-2 ${
                activeTab === 'images'
                  ? 'border-violet-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              Optimisation d'images
            </button>
            <button
              onClick={() => setActiveTab('pdf')}
              className={`px-6 py-4 font-semibold transition-all duration-300 border-b-2 ${
                activeTab === 'pdf'
                  ? 'border-violet-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              Réparation PDF
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {activeTab === 'images' ? (
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
                  smoothing={smoothing}
                  setSmoothing={setSmoothing}
                  watermark={watermark}
                  setWatermark={setWatermark}
                  formats={formats}
                  canOptimize={canOptimize}
                  canSmooth={canSmooth}
                  onProcess={handleProcess}
                  isProcessing={isProcessing}
                />
              </div>

              {/* Right Column - Images */}
              <div className="lg:col-span-2">
                {files.length === 0 ? (
                  <DropZone onFilesAdded={handleFilesAdded} modeType="images" />
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
      ) : (
        /* PDF Repair Tab */
        <PDFRepair />
      )}
    </div>
  )
}
