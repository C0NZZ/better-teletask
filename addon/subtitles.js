(async function addSubtitles() {
  const PLAYER_ID = 'player';
  const BASEURL = 'https://test.com/btt'

  const { apiKey } = await browser.storage.local.get('apiKey');
  if (!apiKey) {
    console.warn("[btt-subtitles] no API key set");
    return;
  }

  const path = (typeof window !== 'undefined' && window.location && window.location.pathname) ? window.location.pathname : '';
    const segments = path.split('/').filter(Boolean);
    let last = segments.length ? segments[segments.length - 1] : '';
    last = decodeURIComponent(last || 'index');
    last = encodeURIComponent(last);
    const urls = [
      {
        lang: 'orig',
        name: 'Original',
        url: `${BASEURL}/${last}`,
        localurl: ''
      }
    ]

  async function fetchSubtitle(url) {
    try {
      const response = await fetch(url, {
        headers: { "Authorization": `Bearer ${apiKey}` }
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch subtitle: ${response.statusText}`);
      }
      return await response.text();
    } catch (error) {
      console.error('[btt-subtitles] Error fetching subtitle:', error);
      return null;
    }
  }

  for (const language of urls) {
    const subtitleText = await fetchSubtitle(language.url);
    if (typeof(subtitleText) === 'string') {
      const BLOB = new Blob([subtitleText], { type: 'text/vtt'});
      language.localurl = URL.createObjectURL(BLOB)
    } else console.warn(`[btt-subtitles] no subtitle found for ${language.name} language`)
  }

  const CAPTIONS_TO_ADD = (() => {
    return urls
      .filter(u => u.localurl.length > 0)
      .map(u => ({
        language: u.lang,
        name: u.name,
        url: u.localurl,
        ...(u.lang === 'orig' ? { type: 'default' } : { type: 'auto-generated' })
      }));
  })();
  if (CAPTIONS_TO_ADD.length === 0) {
    console.warn('[btt-subtitles] no subtitles available, aborting subtitle injection')
    return
  }

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
    console.info('[btt-subtitles] subtitles injected successfully');
  } catch (e) {
    console.error('[btt-subtitles] failed to serialize updated configuration', e);
  }
})();