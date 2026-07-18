import { useState, useEffect } from 'react'
import VideoParamsPanel from '../components/params/VideoParamsPanel'
import DropZone from '../components/DropZone'
import ImageGrid from '../components/ImageGrid'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'
import useOptimizationJob from '../hooks/useOptimizationJob'

export default function OptimizeVideos() {
  const upload = useOptimizationJob({ mode: 'optimize_video', trackEventName: 'videos_optimized' })

  const [videoCodec, setVideoCodec] = useState('h264')
  const [videoQuality, setVideoQuality] = useState(28)
  const [resolution, setResolution] = useState('original')
  const [maxFps, setMaxFps] = useState('')
  const [videoCodecs, setVideoCodecs] = useState({})

  useEffect(() => {
    fetch(`${upload.API_BASE}/api/video/formats`)
      .then(res => res.json())
      .then(setVideoCodecs)
      .catch(err => console.error('Erreur chargement codecs vidéo:', err))
  }, [upload.API_BASE])

  const handleUpload = () => {
    upload.handleProcess((formData) => {
      formData.append('codec', videoCodec)
      formData.append('video_quality', videoQuality)
      formData.append('resolution', resolution)
      if (maxFps) formData.append('max_fps', maxFps)
    })
  }

  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!upload.result ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <VideoParamsPanel
                videoCodec={videoCodec} setVideoCodec={setVideoCodec}
                videoQuality={videoQuality} setVideoQuality={setVideoQuality}
                videoCodecs={videoCodecs}
                resolution={resolution} setResolution={setResolution}
                maxFps={maxFps} setMaxFps={setMaxFps}
                prefix={upload.prefix} setPrefix={upload.setPrefix}
                startNumber={upload.startNumber} setStartNumber={upload.setStartNumber}
                canProcess={upload.canProcess}
                onProcess={handleUpload}
                isProcessing={upload.isProcessing}
              />
            </div>

            <div className="lg:col-span-2">
              {upload.files.length === 0 ? (
                <DropZone onFilesAdded={upload.handleFilesAdded} accept="video" />
              ) : (
                <ImageGrid
                  files={upload.files}
                  prefix={upload.prefix}
                  videoCodec={videoCodec}
                  startNumber={upload.startNumber}
                  onRemoveFile={upload.handleRemoveFile}
                  onFilesAdded={upload.handleFilesAdded}
                />
              )}

              {upload.isProcessing && (
                <div className="mt-8">
                  <ProgressLog progress={upload.progress} totalImages={upload.files.length} jobId={upload.jobId} />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            <ResultCard
              result={upload.result}
              onDownload={upload.handleDownload}
              onReset={upload.handleReset}
            />

            {upload.progress.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-white mb-4">Détails du traitement</h3>
                <ProgressLog progress={upload.progress} totalImages={1} jobId={upload.jobId} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
