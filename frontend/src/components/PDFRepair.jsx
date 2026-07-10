import { useState } from 'react'
import { AlertCircle, CheckCircle, Loader, Zap, X } from 'lucide-react'
import DropZone from './DropZone'

const PDF_API_BASE = import.meta.env.VITE_PDF_API_URL || ''

export default function PDFRepair() {
  const [pdfFiles, setPdfFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [mode, setMode] = useState('normal')
  const [repairProgress, setRepairProgress] = useState({})
  const [completedFiles, setCompletedFiles] = useState([])

  const MAX_FILES = 5

  const handlePdfAdded = async (files, fileType) => {
    if (fileType !== 'pdf' || files.length === 0) return

    const newFiles = Array.from(files).slice(0, MAX_FILES - pdfFiles.length)
    const fileList = newFiles.map((file, idx) => ({
      id: Date.now() + idx,
      file: file,
      name: file.name,
      size: file.size,
      status: 'pending',
      error: null,
      validation: null
    }))

    setPdfFiles([...pdfFiles, ...fileList])
  }

  const validatePdf = async (fileObj) => {
    try {
      const formData = new FormData()
      formData.append('file', fileObj.file)

      const response = await fetch(`${PDF_API_BASE}/api/pdf/validate`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erreur validation PDF')
      }

      const data = await response.json()
      
      setPdfFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, status: 'validated', validation: data, error: null }
          : f
      ))
      setRepairProgress(prev => ({ ...prev, [fileObj.id]: 'Validation réussie ✓' }))
      return true
    } catch (err) {
      setPdfFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, status: 'error', error: err.message }
          : f
      ))
      setRepairProgress(prev => ({ ...prev, [fileObj.id]: `Erreur: ${err.message}` }))
      return false
    }
  }

  const repairPdf = async (fileObj) => {
    try {
      setRepairProgress(prev => ({ ...prev, [fileObj.id]: 'Réparation en cours...' }))

      const formData = new FormData()
      formData.append('file', fileObj.file)

      const endpoint = mode === 'smart' ? `${PDF_API_BASE}/api/pdf/smart-repair` : `${PDF_API_BASE}/api/pdf/repair`

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erreur réparation PDF')
      }

      const blob = await response.blob()

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      if (mode === 'smart') {
        const contentDisposition = response.headers.get('Content-Disposition')
        const filenameMatch = contentDisposition?.match(/filename=([^;]+)/)?.[1]
        link.download = filenameMatch?.replace(/"/g, '') || fileObj.file.name.replace('.pdf', '-repaired.pdf')
      } else {
        link.download = fileObj.file.name.replace('.pdf', '-repaired.pdf')
      }
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setPdfFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, status: 'repaired', error: null }
          : f
      ))
      setRepairProgress(prev => ({ ...prev, [fileObj.id]: 'Réparé et téléchargé ✓' }))
      setCompletedFiles(prev => [...prev, fileObj.id])
      return true
    } catch (err) {
      setPdfFiles(prev => prev.map(f => 
        f.id === fileObj.id 
          ? { ...f, status: 'error', error: err.message }
          : f
      ))
      setRepairProgress(prev => ({ ...prev, [fileObj.id]: `Erreur: ${err.message}` }))
      return false
    }
  }

  const startBatchRepair = async () => {
    setLoading(true)
    setStatus('repairing')
    setRepairProgress({})
    setCompletedFiles([])

    for (const fileObj of pdfFiles) {
      if (fileObj.status === 'pending') {
        setPdfFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { ...f, status: 'validating' } : f
        ))
        
        const isValid = await validatePdf(fileObj)
        if (!isValid) continue

        setPdfFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { ...f, status: 'repairing' } : f
        ))
        
        await repairPdf(fileObj)
      }
    }

    setLoading(false)
    setStatus('completed')
  }

  const removeFile = (id) => {
    setPdfFiles(prev => prev.filter(f => f.id !== id))
    setRepairProgress(prev => {
      const newProgress = { ...prev }
      delete newProgress[id]
      return newProgress
    })
  }

  const resetForm = () => {
    setPdfFiles([])
    setStatus(null)
    setRepairProgress({})
    setCompletedFiles([])
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-slate-400'
      case 'validating':
      case 'repairing': return 'text-blue-400'
      case 'validated':
      case 'repaired': return 'text-green-400'
      case 'error': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'validating':
      case 'repairing': return '⚙️'
      case 'validated':
      case 'repaired': return '✓'
      case 'error': return '✗'
      default: return '○'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">
            Réparation de PDF
          </h1>
          <p className="text-slate-400 text-lg">
            Réparez jusqu'à 5 fichiers PDF corrompus simultanément
          </p>
        </div>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Upload Section */}
          {pdfFiles.length < MAX_FILES && !loading && (
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8">
              <DropZone
                onFilesAdded={handlePdfAdded}
                modeType="pdf"
              />
              <p className="text-center text-slate-400 text-sm mt-4">
                {pdfFiles.length}/{MAX_FILES} fichiers sélectionnés
              </p>
            </div>
          )}

          {/* Files List */}
          {pdfFiles.length > 0 && (
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 space-y-6">
              {/* Mode Selection */}
              <div className="bg-slate-800/50 rounded-2xl p-6 space-y-4 mb-6">
                <h3 className="text-white font-semibold mb-4">Mode de réparation</h3>
                <div className="flex gap-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="normal"
                      checked={mode === 'normal'}
                      onChange={(e) => setMode(e.target.value)}
                      disabled={loading}
                      className="w-4 h-4"
                    />
                    <div>
                      <span className="text-slate-300 font-medium">Standard</span>
                      <p className="text-sm text-slate-500">Réparation simple du PDF</p>
                    </div>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="smart"
                      checked={mode === 'smart'}
                      onChange={(e) => setMode(e.target.value)}
                      disabled={loading}
                      className="w-4 h-4"
                    />
                    <div>
                      <span className="text-slate-300 font-medium">Smart (Intelligent)</span>
                      <p className="text-sm text-slate-500">Analyse + réparation + renommage automatique</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Files List */}
              <div className="space-y-3">
                <h3 className="text-white font-semibold">Fichiers à traiter</h3>
                {pdfFiles.map((fileObj, idx) => (
                  <div key={fileObj.id} className="bg-slate-800/50 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`text-lg ${getStatusColor(fileObj.status)}`}>
                          {getStatusIcon(fileObj.status)}
                        </span>
                        <p className="text-white font-medium truncate">{idx + 1}. {fileObj.name}</p>
                        <span className="text-xs text-slate-500">({formatBytes(fileObj.size)})</span>
                      </div>
                      <p className={`text-sm ${fileObj.status === 'error' ? 'text-red-400' : 'text-slate-400'}`}>
                        {repairProgress[fileObj.id] || 'En attente...'}
                      </p>
                    </div>
                    {!loading && (
                      <button
                        onClick={() => removeFile(fileObj.id)}
                        className="ml-4 p-2 hover:bg-slate-700 rounded-lg transition-colors"
                        title="Supprimer ce fichier"
                      >
                        <X className="w-4 h-4 text-slate-400" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Metadata Summary */}
              {pdfFiles.some(f => f.validation) && (
                <div className="bg-slate-800/50 rounded-2xl p-6">
                  <h3 className="text-white font-semibold mb-3">Résumé validation</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {pdfFiles.map((fileObj) => fileObj.validation && (
                      <div key={fileObj.id} className="text-sm">
                        <p className="text-slate-400 text-xs uppercase tracking-wide mb-1">{fileObj.name}</p>
                        <div className="space-y-1">
                          <p className="text-slate-300">
                            Pages: <span className="text-white font-semibold">{fileObj.validation.pages || '—'}</span>
                          </p>
                          <p className="text-slate-300">
                            Statut: <span className={fileObj.validation.is_valid ? 'text-green-400' : 'text-yellow-400'}>
                              {fileObj.validation.is_valid ? 'Valide' : 'Corrompu'}
                            </span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={startBatchRepair}
                  disabled={pdfFiles.length === 0 || loading}
                  className={`flex-1 px-6 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ${
                    loading || pdfFiles.length === 0
                      ? 'bg-slate-600 text-slate-300 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white'
                  }`}
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Traitement en cours...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Réparer tous les fichiers
                    </>
                  )}
                </button>
                {pdfFiles.length > 0 && (
                  <button
                    onClick={resetForm}
                    disabled={loading}
                    className="px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-600 text-white rounded-xl font-semibold transition-colors"
                  >
                    Réinitialiser
                  </button>
                )}
              </div>

              {/* Success Message */}
              {status === 'completed' && completedFiles.length > 0 && (
                <div className="bg-green-900/30 border border-green-500/50 rounded-xl p-4 flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-green-400 font-semibold">
                      {completedFiles.length}/{pdfFiles.length} fichier(s) réparé(s) avec succès!
                    </p>
                    <p className="text-green-300 text-sm mt-1">
                      Les fichiers réparés ont été téléchargés automatiquement.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* How It Works */}
          {pdfFiles.length === 0 && (
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8">
              <h3 className="text-white font-semibold mb-6">Comment fonctionne la réparation?</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-600/30 rounded-lg flex items-center justify-center text-blue-400 font-bold">
                    1
                  </div>
                  <div>
                    <p className="text-white font-semibold mb-1">Validation</p>
                    <p className="text-slate-400 text-sm">
                      Le système analyse la structure interne de vos PDFs pour détecter les corruptions
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-cyan-600/30 rounded-lg flex items-center justify-center text-cyan-400 font-bold">
                    2
                  </div>
                  <div>
                    <p className="text-white font-semibold mb-1">Réparation</p>
                    <p className="text-slate-400 text-sm">
                      Les objets corrompus sont supprimés et la table de référence croisée (xref) est reconstruite
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-green-600/30 rounded-lg flex items-center justify-center text-green-400 font-bold">
                    3
                  </div>
                  <div>
                    <p className="text-white font-semibold mb-1">Téléchargement</p>
                    <p className="text-slate-400 text-sm">
                      Les fichiers réparés et optimisés sont immédiatement disponibles au téléchargement
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
