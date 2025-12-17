(async function() {
  const player = document.querySelector('video-player');
  if (!player) {
    console.warn("[btt-tweaks] video player not found, couldn't apply tweaks")
    return;
  }
  const { featureSettings } = await browser.storage.local.get('featureSettings');

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
    const videoContainer = player.shadowRoot && player.shadowRoot.getElementById('video-container');
    const path = (typeof e.composedPath === 'function') ? e.composedPath() : (e.path || []);
    if (!path.includes(videoContainer)) return;

    const fsBtn = player.shadowRoot && (player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('full-screen-control').shadowRoot.getElementById('button__fullscreen'));
    if (fsBtn && typeof fsBtn.click === 'function') fsBtn.click();
  }, true);

  //k -> play/pause     &     +/- -> resize subtitles
  document.addEventListener('keydown', e=>{
    switch (e.key.toLowerCase()) {
      case 'k': if (featureSettings?.kplay) {
        const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.getElementById('button__play_pause');
        playBtn.click();
        break;
      }
      case '+': case '-': if (featureSettings?.resizesubs) {
        const subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
        subs.style.fontSize = (parseInt(window.getComputedStyle(subs, null).getPropertyValue('font-size'), 10) + (e.key == '+' ? 5 : -5)).toString() + "px";
        break;
      }
      case 'r': if  (featureSettings?.movesubs) {
        const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
        subbox.removeAttribute('style');
        break;
      }
      default: return;
    }
  });

  //drag subs
  if (featureSettings?.movesubs) {
    const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
    
    let draggingSubs = false;
    subbox.addEventListener("mousedown", (e) => {
      const path = (typeof e.composedPath === 'function') ? e.composedPath() : (e.path || []);
      if (!path.includes(subbox)) return;
      draggingSubs = true;
      const rect = subbox.getBoundingClientRect();
      offsetX = e.clientX - rect.left;
      offsetY = e.clientY - rect.top;
    });

    document.addEventListener("mouseup", () => {
      if (draggingSubs) {
        draggingSubs = false;
      }
    });

    document.addEventListener("mousemove", (e) => {
      if (draggingSubs) {
        const parentRect = player.shadowRoot.getElementById('video-player-container').getBoundingClientRect();
        subbox.style.left = (e.clientX - parentRect.left - offsetX) + "px";
        subbox.style.top  = (e.clientY - parentRect.top  - offsetY + 5) + "px"; //5 counters the bottom in upstream, cant be set before cause it would fuck up when a click without dragging happens
      }
    });
  }

  console.info('[btt-tweaks] tweaks applied successfully');
})();