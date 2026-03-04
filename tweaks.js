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

export async function setSubtitleStyle(settings, player) {
  if (settings?.subcontrast || settings?.subtitleFont) {
    let subs = null;
    for (let i = 0; i < 100 && !subs; i++) {
      subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
      if (!subs) await new Promise(resolve => setTimeout(resolve, 100));
    }

    let fontName = settings.subtitleFont
    if (fontName) {

      let transcript = null;
      for (let i = 0; i < 100 && !transcript; i++) {
        transcript = player.shadowRoot.querySelector('interactive-transcript').shadowRoot.getElementById("container__interactive_transcript");
        if (!transcript) await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (!document.getElementById('btt-fonts-css')) {
        const link = document.createElement('link');
        link.id = 'btt-fonts-css';
        link.rel = 'stylesheet';
        link.href = browser.runtime.getURL('fonts/fonts.css');
        document.head.appendChild(link);
        await new Promise(resolve => {
          link.addEventListener('load', resolve, { once: true });
          link.addEventListener('error', resolve, { once: true });
        });

        if (subs) {
          subs.style.fontFamily = `"${fontName}"`;
          console.info('[btt-subtitles] subtitle font set to', fontName);
        }
        else console.warn('[btt-subtitles] subtitle container not found, font not applied');
        if (transcript) {
          transcript.style.fontFamily = `"${fontName}"`;
          console.info('[btt-subtitles] transcript font set to', fontName);
        }
        else console.warn('[btt-subtitles] transcript container not found, font not applied');
      }
    }

    if (settings?.subcontrast) {
      subs.style.backgroundColor = 'rgb(0, 0, 0)'
    }
  }
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
      }
      break;
      case '+': case '-': if (featureSettings?.editsubstyle) {
        const subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
        subs.style.fontSize = (parseInt(window.getComputedStyle(subs, null).getPropertyValue('font-size'), 10) + (e.key == '+' ? 5 : -5)).toString() + "px";
      }
      break;
      case 'r': if  (featureSettings?.editsubstyle) {
        const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
        subbox.removeAttribute('style');
        subbox.querySelector('.caption-cue-text').removeAttribute('style');
      }
      break;
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