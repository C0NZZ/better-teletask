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
      kplay: true,
    }
    await browser.storage.local.set({ featureSettings });
  }
  
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

  //k press -> play/pause
  document.addEventListener('keydown', e=>{
    if (e.key.toLowerCase() !== 'k') return;
    
    if (!featureSettings?.kplay) return;

    const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.querySelector('#button__play_pause');
    if (playBtn && typeof playBtn.click === 'function') playBtn.click();
  });

  console.info('[btt-tweaks] tweaks applied successfully');
})();