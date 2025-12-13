(async function() {
  const player = document.querySelector('video-player');
  if (!player) {
    console.warn("[btt-tweaks] video player not found, couldn't apply tweaks")
    return;
  }
  const { featureSettings } = await browser.storage.local.get('featureSettings');
  if (!featureSettings) {
    const featureSettings = {
        subtitles: true,
        doubleclick: true,
        noresizelimit: true,
        kplay: true,
    }
    await browser.storage.local.set({ featureSettings });
  }

  if (featureSettings?.noresizelimit) {
    const script = document.createElement('script');
    script.textContent = `
        const videoPlayer = document.querySelector('video-player');
        const dualStream = videoPlayer.shadowRoot.querySelector('dual-stream');
        dualStream._ensureWidthPercentage = (percentage) => Math.max(0, Math.min(1, percentage));
    `;
    
    (document.head || document.documentElement).appendChild(script);
    script.remove();
  };
  
  //doubleclick -> fullscreen
  document.addEventListener('dblclick', e=>{
    if (!featureSettings?.doubleclick) return;

    //only execute when dblclick happens inside video
    const videoContainer = player.shadowRoot && player.shadowRoot.querySelector('#video-container');
    const path = (typeof e.composedPath === 'function') ? e.composedPath() : (e.path || []);
    if (!path.includes(videoContainer)) return;

    const fsBtn = player.shadowRoot && (player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('full-screen-control').shadowRoot.querySelector('#button__fullscreen'));
    if (fsBtn && typeof fsBtn.click === 'function') fsBtn.click();
  }, true);

  //k press -> play/pause     &     +/- resize subtitles
  document.addEventListener('keydown', e=>{
    if (e.key.toLowerCase() == 'k' || e.key == '+' || e.key == '-') {    
      if (e.key.toLowerCase() == 'k' && featureSettings?.kplay) {
        const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.querySelector('#button__play_pause');
        if (playBtn && typeof playBtn.click === 'function') playBtn.click();
      } else if ((e.key == '+' || e.key == '-') && featureSettings?.resizesubs) {
        const subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
        subs.style.fontSize = (parseInt(window.getComputedStyle(subs, null).getPropertyValue('font-size'), 10) + (e.key == '+' ? 5 : -5)).toString() + "px";
      }
    } else return;
  });

  console.info('[btt-tweaks] tweaks applied successfully');
})();