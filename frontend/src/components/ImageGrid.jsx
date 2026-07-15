import { useState, useRef, useEffect } from 'react'
import { X, Upload, FileImage, Film, Play } from 'lucide-react'

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']
const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/x-flv', 'video/x-ms-wmv', 'video/3gpp']
const ALL_ACCEPTED_TYPES = [...ACCEPTED_IMAGE_TYPES, ...ACCEPTED_VIDEO_TYPES]
const ACCEPTED_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.bmp,.tiff,.mp4,.webm,.avi,.mov,.mkv,.flv,.wmv,.m4v,.3gp'

const VIDEO_EXTENSIONS = new Set(['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp'])

function isVideoFile(filename) {
  const ext = filename.toLowerCase().split('.').pop()
  return VIDEO_EXTENSIONS.has(`.${ext}`)
}

function getFileExtension(format) {
  const extensions = {
    jpeg: '.jpg',
    webp: '.webp',
    avif: '.avif',
    png: '.png',
    h264: '.mp4',
    h265: '.mp4',
    vp9: '.webm',
    av1: '.webm',
  }
  return extensions[format] || '.jpg'
}

function formatSize(bytes) {
  if (bytes >= 1_000_000) {
    return `${(bytes / 1_000_000).toFixed(1)} Mo`
  }
  return `${(bytes / 1_000).toFixed(0)} Ko`
}

export default function ImageGrid({ files, prefix, format, videoCodec, startNumber, onRemoveFile, onFilesAdded }) {
  const [previewUrls, setPreviewUrls] = useState({})
  const fileInputRef = useRef(null)

  const getPreviewUrl = (file, index) => {
    if (!previewUrls[index]) {
      const url = URL.createObjectURL(file)
      setPreviewUrls(prev => ({ ...prev, [index]: url }))
      return url
    }
    return previewUrls[index]
  }

  // Cleanup object URLs on unmount
  useEffect(() => {
    return () => {
      Object.values(previewUrls).forEach(url => URL.revokeObjectURL(url))
    }
  }, [previewUrls])

  const handleFileSelect = (e) => {
    const newFiles = Array.from(e.target.files).filter(file =>
      ALL_ACCEPTED_TYPES.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|webp|bmp|tiff|mp4|webm|avi|mov|mkv|flv|wmv|m4v|3gp)$/i)
    )

    if (newFiles.length > 0) {
      onFilesAdded(newFiles)
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  const imageCount = files.filter(f => !isVideoFile(f.name)).length
  const videoCount = files.filter(f => isVideoFile(f.name)).length

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-white">
            Fichiers à optimiser ({files.length})
          </h2>
          <div className="flex gap-2">
            {imageCount > 0 && (
              <span className="px-2 py-0.5 bg-cyan-900/30 text-cyan-300 text-xs font-medium rounded-full border border-cyan-500/20">
                {imageCount} image{imageCount > 1 ? 's' : ''}
              </span>
            )}
            {videoCount > 0 && (
              <span className="px-2 py-0.5 bg-violet-900/30 text-violet-300 text-xs font-medium rounded-full border border-violet-500/20">
                {videoCount} vidéo{videoCount > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleBrowseClick}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-3xl transition-all duration-300"
        >
          <Upload className="w-4 h-4" />
          Ajouter
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {files.map((file, index) => {
          const isVideo = isVideoFile(file.name)
          const futureNumber = startNumber + index
          const ext = isVideo
            ? getFileExtension(videoCodec || 'h264')
            : getFileExtension(format)
          const futureName = `${prefix || 'file'}-${String(futureNumber).padStart(2, '0')}${ext}`

          return (
            <div
              key={index}
              className={`group relative bg-slate-900 border rounded-[2rem] overflow-hidden transition-all duration-300 ${
                isVideo
                  ? 'border-violet-500/30 hover:border-violet-500/60'
                  : 'border-slate-800 hover:border-violet-500/50'
              }`}
            >
              {/* Remove Button */}
              <button
                onClick={() => onRemoveFile(index)}
                className="absolute top-2 right-2 z-10 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-all duration-300 opacity-0 group-hover:opacity-100"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Type Badge */}
              {isVideo && (
                <div className="absolute top-2 left-2 z-10 px-2 py-1 bg-violet-600/90 text-white text-[10px] font-bold rounded-lg flex items-center gap-1">
                  <Film className="w-3 h-3" />
                  VIDÉO
                </div>
              )}

              {/* Preview */}
              <div className="aspect-square bg-slate-800 relative overflow-hidden">
                {isVideo ? (
                  <div className="w-full h-full flex flex-col items-center justify-center">
                    <video
                      src={getPreviewUrl(file, index)}
                      className="w-full h-full object-cover"
                      muted
                      preload="metadata"
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <Play className="w-6 h-6 text-white ml-1" />
                      </div>
                    </div>
                  </div>
                ) : file.type.startsWith('image/') ? (
                  <img
                    src={getPreviewUrl(file, index)}
                    alt={file.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <FileImage className="w-12 h-12 text-slate-600" />
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="p-3 space-y-2">
                <p className="text-sm text-slate-400 truncate" title={file.name}>
                  {file.name}
                </p>
                <p className="text-xs text-slate-500">
                  {formatSize(file.size)}
                </p>
                <div className="pt-2 border-t border-slate-800">
                  <p className={`text-xs font-medium truncate ${isVideo ? 'text-violet-400' : 'text-cyan-400'}`} title={futureName}>
                    → {futureName}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
