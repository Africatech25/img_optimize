import { useState, useRef } from 'react'
import { Upload, Image as ImageIcon, Film } from 'lucide-react'

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']
const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/x-flv', 'video/x-ms-wmv', 'video/3gpp']
const ALL_ACCEPTED_TYPES = [...ACCEPTED_IMAGE_TYPES, ...ACCEPTED_VIDEO_TYPES]

const ACCEPTED_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.bmp,.tiff,.mp4,.webm,.avi,.mov,.mkv,.flv,.wmv,.m4v,.3gp'

export default function DropZone({ onFilesAdded }) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDragIn = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true)
    }
  }

  const handleDragOut = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files).filter(file =>
      ALL_ACCEPTED_TYPES.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|webp|bmp|tiff|mp4|webm|avi|mov|mkv|flv|wmv|m4v|3gp)$/i)
    )

    if (files.length > 0) {
      onFilesAdded(files)
    }
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files).filter(file =>
      ALL_ACCEPTED_TYPES.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|webp|bmp|tiff|mp4|webm|avi|mov|mkv|flv|wmv|m4v|3gp)$/i)
    )

    if (files.length > 0) {
      onFilesAdded(files)
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`relative border-2 border-dashed rounded-[2.5rem] p-12 transition-all duration-300 ${
        isDragging
          ? 'border-violet-500 bg-violet-500/10'
          : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS}
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="flex flex-col items-center justify-center text-center space-y-6">
        {/* Icon */}
        <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
          isDragging
            ? 'bg-gradient-to-br from-violet-600 to-violet-800 scale-110'
            : 'bg-slate-800'
        }`}>
          {isDragging ? (
            <Upload className="w-10 h-10 text-white animate-bounce" />
          ) : (
            <div className="flex items-center gap-2">
              <ImageIcon className="w-8 h-8 text-slate-400" />
              <Film className="w-8 h-8 text-slate-500" />
            </div>
          )}
        </div>

        {/* Text */}
        <div>
          <h3 className="text-2xl font-semibold text-white mb-2">
            {isDragging ? 'Déposez vos fichiers ici' : 'Glissez et déposez vos images ou vidéos'}
          </h3>
          <p className="text-slate-400 mb-6">
            ou cliquez sur le bouton ci-dessous pour parcourir
          </p>

          <button
            onClick={handleBrowseClick}
            className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-2xl transition-all duration-300 hover:scale-105"
          >
            Parcourir les fichiers
          </button>
        </div>

        {/* Accepted formats */}
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2 justify-center">
            {['JPG', 'PNG', 'WebP', 'BMP', 'TIFF'].map(fmt => (
              <span
                key={fmt}
                className="px-3 py-1 bg-slate-800 text-slate-400 text-xs font-medium rounded-full"
              >
                {fmt}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 justify-center">
            {['MP4', 'WebM', 'AVI', 'MOV', 'MKV'].map(fmt => (
              <span
                key={fmt}
                className="px-3 py-1 bg-violet-900/30 text-violet-300 text-xs font-medium rounded-full border border-violet-500/20"
              >
                {fmt}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
