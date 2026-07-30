import { useState, useEffect } from 'react'
import UrlDownloadPanel from '../components/params/UrlDownloadPanel'
import ProgressLog from '../components/ProgressLog'
import ResultCard from '../components/ResultCard'
import useDownloadJob from '../hooks/useDownloadJob'

export default function DownloadVideo() {
  const download = useDownloadJob({ trackEventName: 'videos_downloaded' })

  const [videoCodec, setVideoCodec] = useState('h264')
  const [videoQuality, setVideoQuality] = useState(28)
  const [resolution, setResolution] = useState('original')
  const [maxFps, setMaxFps] = useState('')
  const [videoCodecs, setVideoCodecs] = useState({})

  useEffect(() => {
    fetch(`${download.API_BASE}/api/video/formats`)
      .then(res => res.json())
      .then(setVideoCodecs)
      .catch(err => console.error('Erreur chargement codecs vidéo:', err))
  }, [download.API_BASE])

  const handleDownload = () => {
    download.handleProcess((formData) => {
      formData.append('optimize', download.optimize)
      if (download.optimize) {
        formData.append('codec', videoCodec)
        formData.append('video_quality', videoQuality)
        formData.append('resolution', resolution)
        if (maxFps) formData.append('max_fps', maxFps)
      }
      if (download.cookies.trim()) formData.append('cookies', download.cookies)
    })
  }

  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!download.result ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <UrlDownloadPanel
                url={download.url} setUrl={download.setUrl}
                cookies={download.cookies} setCookies={download.setCookies}
                optimize={download.optimize} setOptimize={download.setOptimize}
                videoCodec={videoCodec} setVideoCodec={setVideoCodec}
                videoQuality={videoQuality} setVideoQuality={setVideoQuality}
                videoCodecs={videoCodecs}
                resolution={resolution} setResolution={setResolution}
                maxFps={maxFps} setMaxFps={setMaxFps}
                prefix={download.prefix} setPrefix={download.setPrefix}
                startNumber={download.startNumber} setStartNumber={download.setStartNumber}
                platforms={download.platforms}
                downloadAvailable={download.downloadAvailable}
                maxSizeMb={download.maxSizeMb}
                urlError={download.urlError}
                canProcess={download.canProcess}
                onProcess={handleDownload}
                isProcessing={download.isProcessing}
              />
            </div>

            <div className="lg:col-span-2">
              <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-10 text-center text-slate-400">
                Collez une URL vidéo (YouTube, TikTok, Facebook...) dans le panneau de gauche,
                choisissez si vous souhaitez l'optimiser, puis lancez le téléchargement.
              </div>

              {download.isProcessing && (
                <div className="mt-8">
                  <ProgressLog progress={download.progress} totalImages={1} jobId={download.jobId} />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            <ResultCard
              result={download.result}
              onDownload={download.handleDownload}
              onReset={download.handleReset}
            />

            {download.progress.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-white mb-4">Détails du traitement</h3>
                <ProgressLog progress={download.progress} totalImages={1} jobId={download.jobId} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
