import { CheckCircle, XCircle, Loader2, Zap, Download, Film, Image as ImageIcon } from 'lucide-react'

export default function ProgressLog({ progress, totalImages, jobId }) {
  const processedCount = progress.filter(p =>
    p.type === 'image_processed' || p.type === 'video_processed' || p.type === 'file_processed'
  ).length
  const progressPercent = totalImages > 0 ? (processedCount / totalImages) * 100 : 0

  const API_BASE = import.meta.env.VITE_API_URL || '';

  const handleDownloadSingle = async (filename) => {
    try {
      const response = await fetch(`${API_BASE}/api/download/${jobId}/${filename}`)
      if (!response.ok) throw new Error('Erreur téléchargement')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Erreur téléchargement:', error)
      alert('Erreur lors du téléchargement')
    }
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2rem] p-6 space-y-4">
      {/* Header with Progress Bar */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Progression</h3>
          <span className="text-sm text-slate-400">
            {processedCount} / {totalImages} fichiers
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-violet-600 to-cyan-600 transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Log Entries */}
      <div className="max-h-96 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900">
        {progress.map((entry, index) => (
          <LogEntry key={index} entry={entry} onDownload={handleDownloadSingle} />
        ))}
      </div>
    </div>
  )
}

function LogEntry({ entry, onDownload }) {
  if (entry.type === 'started') {
    return (
      <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-xl animate-fade-in">
        <Zap className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300">{entry.message}</p>
          <p className="text-xs text-slate-500">{new Date(entry.timestamp).toLocaleTimeString()}</p>
        </div>
      </div>
    )
  }

  if (entry.type === 'batch_started') {
    return (
      <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-xl animate-fade-in">
        <Loader2 className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5 animate-spin" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300">{entry.message}</p>
          <p className="text-xs text-slate-500">{new Date(entry.timestamp).toLocaleTimeString()}</p>
        </div>
      </div>
    )
  }

  // Image processed
  if (entry.type === 'image_processed') {
    if (entry.success) {
      return (
        <div className="flex items-start gap-3 p-3 bg-green-500/5 border border-green-500/20 rounded-xl animate-fade-in group">
          <ImageIcon className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-300 truncate">
              <span className="font-medium">{entry.original_name}</span> → {entry.optimized_name}
            </p>
            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
              <span>{entry.before_formatted} → {entry.after_formatted}</span>
              <span className="text-green-400 font-medium">-{entry.gain_percent}%</span>
            </div>
          </div>
          <button
            onClick={() => onDownload(entry.optimized_name)}
            className="flex-shrink-0 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all opacity-0 group-hover:opacity-100"
            title="Télécharger"
          >
            <Download className="w-4 h-4 text-violet-400" />
          </button>
        </div>
      )
    } else {
      return (
        <div className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-xl animate-fade-in">
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-300 truncate">
              <span className="font-medium">{entry.original_name}</span>
            </p>
            <p className="text-xs text-red-400 mt-1">{entry.error || 'Erreur lors du traitement'}</p>
          </div>
        </div>
      )
    }
  }

  // Video processed (ou téléchargée sans optimisation, entry.optimized === false)
  if (entry.type === 'video_processed') {
    if (entry.success) {
      const wasOptimized = entry.optimized !== false
      return (
        <div className={`flex items-start gap-3 p-3 rounded-xl animate-fade-in group ${wasOptimized ? 'bg-violet-500/5 border border-violet-500/20' : 'bg-slate-800/40 border border-slate-700'}`}>
          {wasOptimized
            ? <Film className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
            : <Download className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
          }
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-300 truncate">
              <span className="font-medium">{entry.original_name}</span> → {entry.optimized_name}
            </p>
            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
              {wasOptimized ? (
                <>
                  <span>{entry.before_formatted} → {entry.after_formatted}</span>
                  <span className="text-violet-400 font-medium">-{entry.gain_percent}%</span>
                </>
              ) : (
                <>
                  <span>{entry.after_formatted}</span>
                  <span className="text-teal-400 font-medium">Sans optimisation</span>
                </>
              )}
              {entry.duration && <span className="text-slate-500">{entry.duration}</span>}
              {entry.resolution && <span className="text-slate-500">{entry.resolution}</span>}
              {entry.codec && <span className="text-slate-500 uppercase">{entry.codec}</span>}
            </div>
          </div>
          <button
            onClick={() => onDownload(entry.optimized_name)}
            className="flex-shrink-0 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all opacity-0 group-hover:opacity-100"
            title="Télécharger"
          >
            <Download className="w-4 h-4 text-violet-400" />
          </button>
        </div>
      )
    } else {
      return (
        <div className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-xl animate-fade-in">
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-300 truncate">
              <span className="font-medium">{entry.original_name}</span>
            </p>
            <p className="text-xs text-red-400 mt-1">{entry.error || 'Erreur lors du traitement vidéo'}</p>
          </div>
        </div>
      )
    }
  }

  if (entry.type === 'completed') {
    return (
      <div className="flex items-start gap-3 p-3 bg-gradient-to-r from-violet-500/10 to-cyan-500/10 border border-violet-500/20 rounded-xl animate-fade-in">
        <CheckCircle className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white font-medium">{entry.message}</p>
          <p className="text-xs text-slate-500">{new Date(entry.timestamp).toLocaleTimeString()}</p>
        </div>
      </div>
    )
  }

  // Image error (legacy)
  if (entry.type === 'image_error') {
    return (
      <div className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-xl animate-fade-in">
        <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300 truncate">
            {entry.original_name && <span className="font-medium">{entry.original_name}</span>}
          </p>
          <p className="text-xs text-red-400 mt-1">{entry.error || 'Erreur inconnue'}</p>
        </div>
      </div>
    )
  }

  // Video error
  if (entry.type === 'video_error') {
    return (
      <div className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-xl animate-fade-in">
        <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-300 truncate">
            {entry.original_name && <span className="font-medium">{entry.original_name}</span>}
          </p>
          <p className="text-xs text-red-400 mt-1">{entry.error || 'Erreur vidéo inconnue'}</p>
        </div>
      </div>
    )
  }

  return null
}
