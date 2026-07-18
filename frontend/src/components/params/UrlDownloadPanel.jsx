import { Download, Lock } from 'lucide-react'

const RESOLUTION_OPTIONS = [
  { value: 'original', label: 'Original' },
  { value: '4k', label: '4K (3840x2160)' },
  { value: '1080p', label: '1080p (1920x1080)' },
  { value: '720p', label: '720p (1280x720)' },
  { value: '480p', label: '480p (854x480)' },
  { value: '360p', label: '360p (640x360)' },
]

export default function UrlDownloadPanel({
  url, setUrl,
  cookies, setCookies,
  prefix, setPrefix,
  startNumber, setStartNumber,
  platforms, downloadAvailable, maxSizeMb,
  urlError, canProcess, onProcess, isProcessing,
  optimize, setOptimize,
  videoCodec, setVideoCodec,
  videoQuality, setVideoQuality,
  videoCodecs,
  resolution, setResolution,
  maxFps, setMaxFps,
}) {
  const currentCodec = videoCodecs?.[videoCodec]
  const crfRange = currentCodec?.crf_range || [18, 51]
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center">
          <Download className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Télécharger par URL</h2>
      </div>

      {!downloadAvailable && (
        <div className="p-3 bg-amber-900/30 border border-amber-700 rounded-xl text-sm text-amber-300">
          Le téléchargement par URL est indisponible sur ce serveur.
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          URL de la vidéo <span className="text-red-400">*</span>
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=... | facebook.com/... | tiktok.com/..."
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
        {urlError && (
          <p className="mt-1 text-xs text-red-400">{urlError}</p>
        )}
        {platforms.length > 0 && (
          <p className="mt-2 text-xs text-slate-500">
            Supporté : {platforms.join(', ')}
          </p>
        )}
      </div>

      <details className="group">
        <summary className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer select-none">
          <Lock className="w-4 h-4" />
          Cookies (optionnel, pour vidéos Facebook privées)
        </summary>
        <textarea
          value={cookies}
          onChange={(e) => setCookies(e.target.value)}
          placeholder="Collez le contenu d'un fichier cookies Netscape (pour FB privé/groupes/stories)"
          rows={4}
          className="mt-2 w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-xs"
          disabled={isProcessing}
        />
      </details>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Préfixe SEO <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="ex: video-vacances-2026"
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Numéro de départ
        </label>
        <input
          type="number"
          min="1"
          value={startNumber}
          onChange={(e) => setStartNumber(parseInt(e.target.value) || 1)}
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      <div className="pt-2 border-t border-slate-800">
        <label className="flex items-center justify-between cursor-pointer select-none">
          <span className="text-sm font-medium text-slate-300">
            Optimiser après téléchargement
          </span>
          <input
            type="checkbox"
            checked={optimize}
            onChange={(e) => setOptimize(e.target.checked)}
            disabled={isProcessing}
            className="w-5 h-5 rounded accent-emerald-500 cursor-pointer"
          />
        </label>
        <p className="mt-1 text-xs text-slate-500">
          Désactivez pour récupérer la vidéo telle quelle, sans compression.
        </p>
      </div>

      {optimize && (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Codec vidéo
            </label>
            <select
              value={videoCodec}
              onChange={(e) => setVideoCodec(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            >
              {Object.entries(videoCodecs || {})
                .filter(([, config]) => config.available !== false)
                .map(([codec]) => (
                  <option key={codec} value={codec}>{codec.toUpperCase()}</option>
                ))}
            </select>
          </div>

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
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer accent-emerald-500"
              disabled={isProcessing}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Résolution
            </label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            >
              {RESOLUTION_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

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
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              disabled={isProcessing}
            />
          </div>
        </div>
      )}

      <p className="text-xs text-slate-500 leading-relaxed">
        Taille max : {maxSizeMb} Mo. Le téléchargement peut enfreindre les CGU
        des plateformes et le droit d'auteur. À utiliser uniquement pour du
        contenu dont vous détenez les droits ou en usage personnel autorisé.
      </p>

      <button
        onClick={onProcess}
        disabled={!canProcess}
        className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
          canProcess
            ? 'bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white shadow-lg hover:shadow-xl hover:scale-105'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing
          ? 'Téléchargement en cours...'
          : optimize ? 'Télécharger & optimiser' : 'Télécharger'}
      </button>
    </div>
  )
}
