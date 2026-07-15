import { Sliders, Film, Image as ImageIcon } from 'lucide-react'

const RESOLUTION_OPTIONS = [
  { value: 'original', label: 'Original' },
  { value: '4k', label: '4K (3840x2160)' },
  { value: '1080p', label: '1080p (1920x1080)' },
  { value: '720p', label: '720p (1280x720)' },
  { value: '480p', label: '480p (854x480)' },
  { value: '360p', label: '360p (640x360)' },
]

export default function ParamsPanel({
  // Image params
  format,
  setFormat,
  quality,
  setQuality,
  formats,
  // Video params
  videoCodec,
  setVideoCodec,
  videoQuality,
  setVideoQuality,
  videoCodecs,
  resolution,
  setResolution,
  maxFps,
  setMaxFps,
  // Common params
  prefix,
  setPrefix,
  startNumber,
  setStartNumber,
  canOptimize,
  onOptimize,
  isProcessing,
  // File info
  hasImages,
  hasVideos,
}) {
  const currentFormat = formats?.[format]
  const qualityRange = currentFormat?.quality_range || [1, 100]

  const currentCodec = videoCodecs?.[videoCodec]
  const crfRange = currentCodec?.crf_range || [18, 51]

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center">
          <Sliders className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Paramètres</h2>
      </div>

      {/* Préfixe SEO */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Préfixe SEO <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="ex: hotel-bretagne-2026"
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
        <p className="mt-1 text-xs text-slate-500">
          Ce préfixe sera utilisé pour nommer vos fichiers
        </p>
      </div>

      {/* ===== PARAMÈTRES IMAGES ===== */}
      {hasImages && (
        <div className="space-y-4 p-4 bg-slate-800/30 rounded-2xl border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <ImageIcon className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">Images</h3>
          </div>

          {/* Format image */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Format de sortie
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            >
              {Object.entries(formats || {})
                .filter(([, config]) => config.available !== false)
                .map(([fmt]) => (
                  <option key={fmt} value={fmt}>
                    {fmt.toUpperCase()}
                  </option>
                ))}
            </select>

            {currentFormat && (
              <div className="mt-2 p-3 bg-slate-800/50 border border-slate-700 rounded-xl">
                <p className="text-xs text-slate-400">
                  {currentFormat.description}
                </p>
              </div>
            )}
          </div>

          {/* Qualité image */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-300">
                {format === 'png' ? 'Niveau de compression' : 'Qualité'}
              </label>
              <span className="text-lg font-bold text-white">{quality}</span>
            </div>
            <input
              type="range"
              min={qualityRange[0]}
              max={qualityRange[1]}
              value={quality}
              onChange={(e) => setQuality(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer accent-cyan-500"
              disabled={isProcessing}
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>{qualityRange[0]}</span>
              <span>{qualityRange[1]}</span>
            </div>
          </div>
        </div>
      )}

      {/* ===== PARAMÈTRES VIDÉOS ===== */}
      {hasVideos && (
        <div className="space-y-4 p-4 bg-violet-900/10 rounded-2xl border border-violet-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Film className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-violet-400 uppercase tracking-wider">Vidéos</h3>
          </div>

          {/* Codec vidéo */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Codec vidéo
            </label>
            <select
              value={videoCodec}
              onChange={(e) => setVideoCodec(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            >
              {Object.entries(videoCodecs || {})
                .filter(([, config]) => config.available !== false)
                .map(([codec]) => (
                  <option key={codec} value={codec}>
                    {codec.toUpperCase()}
                  </option>
                ))}
            </select>

            {currentCodec && (
              <div className="mt-2 p-3 bg-slate-800/50 border border-slate-700 rounded-xl">
                <p className="text-xs text-slate-400">
                  {currentCodec.description}
                </p>
              </div>
            )}
          </div>

          {/* Qualité vidéo (CRF) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-300">
                Qualité (CRF)
              </label>
              <span className="text-lg font-bold text-white">{videoQuality}</span>
            </div>
            <input
              type="range"
              min={crfRange[0]}
              max={crfRange[1]}
              value={videoQuality}
              onChange={(e) => setVideoQuality(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer accent-violet-500"
              disabled={isProcessing}
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>{crfRange[0]} (meilleure)</span>
              <span>{crfRange[1]} (plus petite)</span>
            </div>
          </div>

          {/* Résolution */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Résolution
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            >
              {RESOLUTION_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* FPS max */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              FPS maximum
            </label>
            <input
              type="number"
              min="1"
              max="120"
              value={maxFps}
              onChange={(e) => setMaxFps(parseInt(e.target.value) || '')}
              placeholder="Original"
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            />
            <p className="mt-1 text-xs text-slate-500">
              Laisser vide pour conserver le FPS original
            </p>
          </div>
        </div>
      )}

      {/* Numéro de départ */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Numéro de départ
        </label>
        <input
          type="number"
          min="1"
          value={startNumber}
          onChange={(e) => setStartNumber(parseInt(e.target.value) || 1)}
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      {/* Button */}
      <button
        onClick={onOptimize}
        disabled={!canOptimize}
        className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
          canOptimize
            ? 'bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white shadow-lg hover:shadow-xl hover:scale-105'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing ? 'Optimisation en cours...' : 'Optimiser les fichiers'}
      </button>
    </div>
  )
}
