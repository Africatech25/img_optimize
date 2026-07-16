const STORAGE_KEY = 'imgopt_attribution'

/**
 * Capture le referrer HTTP et les paramètres UTM à la toute première visite
 * (document.referrer n'est disponible qu'au premier chargement de page,
 * pas lors de la navigation interne d'une SPA). Stocké pour être envoyé
 * plus tard, au moment de l'inscription seulement.
 */
export function captureAttribution() {
  if (localStorage.getItem(STORAGE_KEY)) return

  const params = new URLSearchParams(window.location.search)
  const data = {
    referrer: document.referrer || '',
    utm_source: params.get('utm_source') || '',
    utm_medium: params.get('utm_medium') || '',
    utm_campaign: params.get('utm_campaign') || '',
  }

  if (data.referrer || data.utm_source) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }
}

export function getAttribution() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null') || {}
  } catch {
    return {}
  }
}
