import { useState, useRef } from 'react'
import { X, Upload, FileImage } from 'lucide-react'

const ACCEPTED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']

export default function ImageGrid({ files, prefix, format, startNumber, onRemoveFile, onFilesAdded }) {
  const [previewUrls, setPreviewUrls] = useState({})
  const fileInputRef = useRef(null)

  // Créer les URLs de prévisualisation
  const getPreviewUrl = (file, index) => {
    if (!previewUrls[index]) {
      const url = URL.createObjectURL(file)
      setPreviewUrls(prev => ({ ...prev, [index]: url }))
      return url
    }
    return previewUrls[index]
  }

  const formatSize = (bytes) => {
    if (bytes >= 1_000_000) {
      return `${(bytes / 1_000_000).toFixed(1)} Mo`
    }
    return `${(bytes / 1_000).toFixed(0)} Ko`
  }

  const getExtension = () => {
    const extensions = {
      jpeg: '.jpg',
      webp: '.webp',
      avif: '.avif',
      png: '.png'
    }
    return extensions[format] || '.jpg'
  }

  const handleFileSelect = (e) => {
    const newFiles = Array.from(e.target.files).filter(file =>
      ACCEPTED_TYPES.includes(file.type)
    )

    if (newFiles.length > 0) {
      onFilesAdded(newFiles)
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">
          Images à optimiser ({files.length})
        </h2>
        <button
          onClick={handleBrowseClick}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-3xl transition-all duration-300"
        >
          <Upload className="w-4 h-4" />
          Ajouter des images
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {files.map((file, index) => {
          const futureNumber = startNumber + index
          const futureName = `${prefix || 'image'}-${String(futureNumber).padStart(2, '0')}${getExtension()}`

          return (
            <div
              key={index}
              className="group relative bg-slate-900 border border-slate-800 rounded-[2rem] overflow-hidden hover:border-violet-500/50 transition-all duration-300"
            >
              {/* Remove Button */}
              <button
                onClick={() => onRemoveFile(index)}
                className="absolute top-2 right-2 z-10 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-all duration-300 opacity-0 group-hover:opacity-100"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Image Preview */}
              <div className="aspect-square bg-slate-800 relative overflow-hidden">
                {file.type.startsWith('image/') ? (
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
                  <p className="text-xs text-violet-400 font-medium truncate" title={futureName}>
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
