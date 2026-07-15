import { useState, useEffect } from 'react'
import ImageParamsPanel from '../components/params/ImageParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'
import useOptimizationJob from '../hooks/useOptimizationJob'

export default function OptimizeImages() {
  const job = useOptimizationJob({ mode: 'optimize_image', trackEventName: 'images_optimized' })

  const [format, setFormat] = useState('webp')
  const [quality, setQuality] = useState(82)
  const [formats, setFormats] = useState({})

  useEffect(() => {
    fetch(`${job.API_BASE}/api/formats`)
      .then(res => res.json())
      .then(setFormats)
      .catch(err => console.error('Erreur chargement formats:', err))
  }, [job.API_BASE])

  useEffect(() => {
    if (formats[format]) {
      setQuality(formats[format].default_quality)
    }
  }, [format, formats])

  const handleOptimize = () => {
    job.handleProcess((formData) => {
      formData.append('format', format)
      formData.append('quality', quality)
    })
  }

  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!job.result ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <ImageParamsPanel
                format={format} setFormat={setFormat}
                quality={quality} setQuality={setQuality}
                formats={formats}
                prefix={job.prefix} setPrefix={job.setPrefix}
                startNumber={job.startNumber} setStartNumber={job.setStartNumber}
                canProcess={job.canProcess}
                onProcess={handleOptimize}
                isProcessing={job.isProcessing}
              />
            </div>

            <div className="lg:col-span-2">
              {job.files.length === 0 ? (
                <DropZone onFilesAdded={job.handleFilesAdded} accept="image" />
              ) : (
                <ImageGrid
                  files={job.files}
                  prefix={job.prefix}
                  format={format}
                  startNumber={job.startNumber}
                  onRemoveFile={job.handleRemoveFile}
                  onFilesAdded={job.handleFilesAdded}
                />
              )}

              {job.isProcessing && (
                <div className="mt-8">
                  <ProgressLog progress={job.progress} totalImages={job.files.length} jobId={job.jobId} />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            <ResultCard
              result={job.result}
              onDownload={job.handleDownload}
              onReset={job.handleReset}
            />

            {job.progress.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-white mb-4">Détails du traitement</h3>
                <ProgressLog progress={job.progress} totalImages={job.files.length} jobId={job.jobId} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
