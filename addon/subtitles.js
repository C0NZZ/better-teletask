(async function addSubtitles() {
  const PLAYER_ID = 'player';

  const path = (typeof window !== 'undefined' && window.location && window.location.pathname) ? window.location.pathname : '';
    const segments = path.split('/').filter(Boolean);
    let last = segments.length ? segments[segments.length - 1] : '';
    last = decodeURIComponent(last || 'index');
    last = encodeURIComponent(last);
    const suburl = `https://test.com/btt/${last}/de`

  async function fetchSubtitle(url) {
    try {
      const response = await fetch(suburl);
      if (!response.ok) {
        throw new Error(`Failed to fetch subtitle: ${response.statusText}`);
      }
      return await response.text();
    } catch (error) {
      console.error('[btt-subtitles] Error fetching subtitle:', error);
      return null;
    }
  }

  const subtitleText = await fetchSubtitle(suburl);
  const BLOB = new Blob([subtitleText], { type: 'text/vtt'});
  const LOCALURL = URL.createObjectURL(BLOB)


  const CAPTIONS_TO_ADD = (() => {
    return [
      {
        language: 'de',
        name: 'Deutsch',
        url: `${LOCALURL}`,
        type: 'default'
      }
    ];
  })();

  function decodeHtmlEntities(str) {
    if (!str || typeof str !== 'string') return str;
    const txt = document.createElement('textarea');
    txt.innerHTML = str;
    return txt.value;
  }

  function safeJsonParse(str) {
    if (typeof str !== 'string') return null;
    let s = str.trim();

    s = decodeHtmlEntities(s);
    if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
      s = s.slice(1, -1);
    }

    const attempts = [
      s,
      s.replace(/&quot;/g, '"'),
      s.replace(/&amp;/g, '&'),
      s.replace(/\\"/g, '"')
    ];

    for (const attempt of attempts) {
      try {
        return JSON.parse(attempt);
      } catch (e) {
      }
    }
    return null;
  }

  const playerEl = document.getElementById(PLAYER_ID);
  if (!playerEl) {
    console.warn(`[btt-subtitles] element with id="${PLAYER_ID}" not found`);
    return;
  }

  const raw = playerEl.getAttribute('configuration');
  if (!raw) {
    console.warn('[btt-subtitles] no configuration attribute found on element');
    return;
  }

  const config = safeJsonParse(raw);
  if (!config || typeof config !== 'object') {
    console.warn('[btt-subtitles] failed to parse configuration JSON');
    return;
  }

  config.captions = CAPTIONS_TO_ADD;

  try {
    const serialized = JSON.stringify(config);
    playerEl.setAttribute('configuration', serialized);
    // playerEl.setAttribute('configuration', serialized.replace(/"/g, '&quot;'));
    console.info('[btt-subtitles] configuration attribute updated successfully');
  } catch (e) {
    console.error('[btt-subtitles] failed to serialize updated configuration', e);
  }
})();