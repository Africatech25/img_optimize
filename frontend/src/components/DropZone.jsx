import { useState, useRef } from 'react'
import { Upload, Image as ImageIcon, Film } from 'lucide-react'

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']
const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/x-flv', 'video/x-ms-wmv', 'video/3gpp']

const IMAGE_EXT_REGEX = /\.(jpg|jpeg|png|webp|bmp|tiff)$/i
const VIDEO_EXT_REGEX = /\.(mp4|webm|avi|mov|mkv|flv|wmv|m4v|3gp)$/i

const PROFILES = {
  image: {
    types: ACCEPTED_IMAGE_TYPES,
    extRegex: IMAGE_EXT_REGEX,
    extensionsAttr: '.jpg,.jpeg,.png,.webp,.bmp,.tiff',
    badges: [{ label: ['JPG', 'PNG', 'WebP', 'BMP', 'TIFF'], style: 'neutral' }],
    label: 'images',
    icon: ImageIcon,
  },
  video: {
    types: ACCEPTED_VIDEO_TYPES,
    extRegex: VIDEO_EXT_REGEX,
    extensionsAttr: '.mp4,.webm,.avi,.mov,.mkv,.flv,.wmv,.m4v,.3gp',
    badges: [{ label: ['MP4', 'WebM', 'AVI', 'MOV', 'MKV'], style: 'accent' }],
    label: 'vidéos',
    icon: Film,
  },
}

export default function DropZone({ onFilesAdded, accept = 'image' }) {
  const profile = PROFILES[accept] || PROFILES.image
  const Icon = profile.icon
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

  const filterFiles = (fileList) => {
    const valid = []
    let rejected = 0

    Array.from(fileList).forEach(file => {
      if (profile.types.includes(file.type) || profile.extRegex.test(file.name)) {
        valid.push(file)
      } else {
        rejected++
      }
    })

    if (rejected > 0) {
      alert(
        `${rejected} fichier(s) ignoré(s) : cette page n'accepte que des ${profile.label} ` +
        `(${profile.extensionsAttr.split(',').join(', ')}).`
      )
    }

    return valid
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = filterFiles(e.dataTransfer.files)
    if (files.length > 0) {
      onFilesAdded(files)
    }
  }

  const handleFileSelect = (e) => {
    const files = filterFiles(e.target.files)
    if (files.length > 0) {
      onFilesAdded(files)
    }
    e.target.value = ''
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
        accept={profile.extensionsAttr}
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
            <Icon className="w-8 h-8 text-slate-400" />
          )}
        </div>

        {/* Text */}
        <div>
          <h3 className="text-2xl font-semibold text-white mb-2">
            {isDragging ? 'Déposez vos fichiers ici' : `Glissez et déposez vos ${profile.label}`}
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
        <div className="flex flex-wrap gap-2 justify-center">
          {profile.badges.flatMap(group => group.label).map(fmt => (
            <span
              key={fmt}
              className={`px-3 py-1 text-xs font-medium rounded-full ${
                accept === 'video'
                  ? 'bg-violet-900/30 text-violet-300 border border-violet-500/20'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {fmt}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
