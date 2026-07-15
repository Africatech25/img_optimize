import { useState } from 'react'
import SignParamsPanel from '../components/params/SignParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'
import useOptimizationJob from '../hooks/useOptimizationJob'

export default function SignImages() {
  const job = useOptimizationJob({ mode: 'sign', trackEventName: 'images_signed' })

  const [watermark, setWatermark] = useState({
    type: 'text',
    text: '',
    logo: null,
    position: 'bottom-right',
    opacity: 70,
  })

  const handleSign = () => {
    job.handleProcess((formData) => {
      formData.append('watermark_type', watermark.type)
      formData.append('watermark_text', watermark.text)
      formData.append('watermark_position', watermark.position)
      formData.append('watermark_opacity', watermark.opacity)
      if (watermark.type === 'image' && watermark.logo) {
        formData.append('watermark_logo', watermark.logo)
      }
    })
  }

  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!job.result ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <SignParamsPanel
                watermark={watermark} setWatermark={setWatermark}
                prefix={job.prefix} setPrefix={job.setPrefix}
                startNumber={job.startNumber} setStartNumber={job.setStartNumber}
                canProcess={job.canProcess}
                onProcess={handleSign}
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
