import { useState, useRef } from 'react'
import { Upload, Image as ImageIcon, File } from 'lucide-react'

const IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']
const PDF_TYPES = ['application/pdf']
const ALL_ACCEPTED_TYPES = [...IMAGE_TYPES, ...PDF_TYPES]

export default function DropZone({ onFilesAdded, modeType = 'auto' }) {
  // modeType: 'auto' (détecte le type), 'images' (images seulement), 'pdf' (PDF seulement)
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

  const classifyFiles = (fileList) => {
    const images = []
    const pdfs = []

    Array.from(fileList).forEach(file => {
      if (IMAGE_TYPES.includes(file.type)) {
        images.push(file)
      } else if (PDF_TYPES.includes(file.type)) {
        pdfs.push(file)
      }
    })

    return { images, pdfs }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const { images, pdfs } = classifyFiles(e.dataTransfer.files)

    if (modeType === 'auto') {
      // Déterminer le type dominant
      if (images.length > 0 && pdfs.length === 0) {
        onFilesAdded(images, 'images')
      } else if (pdfs.length > 0 && images.length === 0) {
        onFilesAdded(pdfs, 'pdf')
      } else if (images.length > 0 && pdfs.length > 0) {
        // Mélange : prioriser les images
        onFilesAdded(images, 'images')
      }
    } else if (modeType === 'images') {
      if (images.length > 0) onFilesAdded(images, 'images')
    } else if (modeType === 'pdf') {
      if (pdfs.length > 0) onFilesAdded(pdfs, 'pdf')
    }
  }

  const handleFileSelect = (e) => {
    const { images, pdfs } = classifyFiles(e.target.files)

    if (modeType === 'auto') {
      if (images.length > 0 && pdfs.length === 0) {
        onFilesAdded(images, 'images')
      } else if (pdfs.length > 0 && images.length === 0) {
        onFilesAdded(pdfs, 'pdf')
      } else if (images.length > 0 && pdfs.length > 0) {
        onFilesAdded(images, 'images')
      }
    } else if (modeType === 'images') {
      if (images.length > 0) onFilesAdded(images, 'images')
    } else if (modeType === 'pdf') {
      if (pdfs.length > 0) onFilesAdded(pdfs, 'pdf')
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  const getAcceptAttribute = () => {
    if (modeType === 'pdf') return '.pdf'
    if (modeType === 'images') return IMAGE_TYPES.join(',')
    return ALL_ACCEPTED_TYPES.join(',')
  }

  const getIcon = () => {
    if (isDragging) {
      return <Upload className="w-10 h-10 text-white animate-bounce" />
    }
    if (modeType === 'pdf') {
      return <File className="w-10 h-10 text-slate-400" />
    }
    return <ImageIcon className="w-10 h-10 text-slate-400" />
  }

  const getTitle = () => {
    if (isDragging) {
      if (modeType === 'pdf') return 'Déposez votre PDF ici'
      if (modeType === 'images') return 'Déposez vos images ici'
      return 'Déposez vos fichiers ici'
    }
    if (modeType === 'pdf') return 'Glissez et déposez votre PDF'
    if (modeType === 'images') return 'Glissez et déposez vos images'
    return 'Glissez et déposez vos fichiers'
  }

  const getSupportedFormats = () => {
    if (modeType === 'pdf') return ['PDF']
    if (modeType === 'images') return ['JPG', 'PNG', 'WebP', 'BMP', 'TIFF']
    return ['JPG', 'PNG', 'WebP', 'BMP', 'TIFF', 'PDF']
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
        multiple={modeType !== 'pdf'}
        accept={getAcceptAttribute()}
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
          {getIcon()}
        </div>

        {/* Text */}
        <div>
          <h3 className="text-2xl font-semibold text-white mb-2">
            {getTitle()}
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
          {getSupportedFormats().map(fmt => (
            <span
              key={fmt}
              className="px-3 py-1 bg-slate-800 text-slate-400 text-xs font-medium rounded-full"
            >
              {fmt}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
