export function removeResizeLimit(featureSettings) {
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
}

export function doubleclickHandler(featureSettings, player) {
  return (e)=>{
    if (!featureSettings?.doubleclick) return;

    //only execute when dblclick happens inside video
    const videoContainer = player.shadowRoot && player.shadowRoot.getElementById('video-container');
    const path = (typeof e.composedPath === 'function') ? e.composedPath() : (e.path || []);
    if (!path.includes(videoContainer)) return;

    const fsBtn = player.shadowRoot && (player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('full-screen-control').shadowRoot.getElementById('button__fullscreen'));
    if (fsBtn && typeof fsBtn.click === 'function') fsBtn.click();
  };
}

export function keydownHandler(featureSettings, player) {
  return (e)=>{
    switch (e.key.toLowerCase()) {
      case 'k': if (featureSettings?.kplay) {
        const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.getElementById('button__play_pause');
        playBtn.click();
        break;
      }
      case '+': case '-': if (featureSettings?.editsubstyle) {
        const subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
        subs.style.fontSize = (parseInt(window.getComputedStyle(subs, null).getPropertyValue('font-size'), 10) + (e.key == '+' ? 5 : -5)).toString() + "px";
        break;
      }
      case 'r': if  (featureSettings?.editsubstyle) {
        const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
        subbox.removeAttribute('style');
        subbox.querySelector('.caption-cue-text').removeAttribute('style');
        break;
      }
      default: return;
    }
  };
}

export function mediasessionHandler(featureSettings, player) {
  return () => {
    if (!featureSettings?.kplay) return;
    const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.getElementById('button__play_pause');
    playBtn.click();
  };
}

export function subtitleDragHandler(featureSettings, player) {
  if (!featureSettings?.editsubstyle) return null;

  const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');

  let draggingSubs = false;
  let offsetX;
  let offsetY;

  const onMouseDown = (e) => {
    const path = (typeof e.composedPath === 'function') ? e.composedPath() : (e.path || []);
    if (!path.includes(subbox)) return;
    draggingSubs = true;
    const rect = subbox.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = rect.bottom - e.clientY;
  };

  const onMouseUp = () => {
    if (draggingSubs) {
      draggingSubs = false;
    }
  };

  const onMouseMove = (e) => {
    if (draggingSubs) {
      const parentRect = subbox.offsetParent.getBoundingClientRect();
      subbox.style.left = (e.clientX - parentRect.left - offsetX) + "px";
      subbox.style.bottom = (parentRect.bottom - e.clientY - offsetY) + "px";
    }
  };

  return { subbox, onMouseDown, onMouseUp, onMouseMove };
}