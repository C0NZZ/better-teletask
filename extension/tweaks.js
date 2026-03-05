export function removeResizeLimit(featureSettings) {
  if (featureSettings?.noresizelimit) {
    const script = document.createElement('script');
    script.textContent = `
        const dualStream = document.querySelector('video-player').shadowRoot.querySelector('dual-stream');
        dualStream._ensureWidthPercentage = (percentage) => Math.max(0, Math.min(1, percentage));
    `;
    
    (document.head || document.documentElement).appendChild(script);
    script.remove();
  };
}

export async function setSubtitleStyle(settings, player) {
  if (settings?.subtitlestyle.font || settings?.subtitlestyle.contrast || settings?.subtitlestyle.moveable) {
    const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
    
    if (settings?.subtitlestyle.font) {
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
      }

      const transcript = player.shadowRoot.querySelector('interactive-transcript').shadowRoot.getElementById("container__interactive_transcript");
      const fontName = settings.subtitlestyle.font
      if (fontName) {
        transcript.style.fontFamily = `"${fontName}"`;
        subbox.style.fontFamily = `"${fontName}"`;
        console.info('[btt-subtitles] captions font set to', fontName);
        window.__stopCaptionSubtitleProbe?.()
      }
    }

    if (settings?.subtitlestyle.contrast) {
      subbox.querySelector('.caption-cue-text').style.backgroundColor = 'rgb(0, 0, 0)';
    }

    if (settings?.subtitlestyle.moveable) {
      if (settings.subtitlestyle.position[0]) {subbox.style.left = settings.subtitlestyle.position[0]};
      if (settings.subtitlestyle.position[1]) {subbox.style.bottom = settings.subtitlestyle.position[1]};
      if (settings.subtitlestyle.size) {subbox.querySelector('.caption-cue-text').style.fontSize = settings.subtitlestyle.size};
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
  return async (e)=>{
    switch (e.key.toLowerCase()) {
      case 'k': if (featureSettings?.kplay) {
        const playBtn = player.shadowRoot && player.shadowRoot.querySelector('control-bar').shadowRoot.querySelector('playpause-control').shadowRoot.getElementById('button__play_pause');
        playBtn.click();
      }
      break;
      case '+': case '-': if (featureSettings?.subtitlestyle.moveable) {
        const subs = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions').querySelector('.caption-cue-text');
        subs.style.fontSize = (parseInt(window.getComputedStyle(subs, null).getPropertyValue('font-size'), 10) + (e.key == '+' ? 5 : -5)).toString() + "px";
        featureSettings.subtitlestyle.size = subs.style.fontSize;
        await browser.storage.local.set({ featureSettings });
      }
      break;
      case 'r': if  (featureSettings?.subtitlestyle.moveable) {
        const subbox = player.shadowRoot.querySelector('captions-display').shadowRoot.getElementById('container__captions');
        subbox.style.removeProperty('left');
        subbox.style.removeProperty('bottom');
        subbox.querySelector('.caption-cue-text').style.removeProperty('font-size');
        featureSettings.subtitlestyle.size = null;
        featureSettings.subtitlestyle.position = [null, null];
        await browser.storage.local.set({ featureSettings });
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
  if (!featureSettings?.subtitlestyle.moveable) return null;

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

  const onMouseUp = async () => {
    if (draggingSubs) {
      draggingSubs = false;
      await browser.storage.local.set({ featureSettings });
    }
  };

  const onMouseMove = (e) => {
    if (draggingSubs) {
      const parentRect = subbox.offsetParent.getBoundingClientRect();
      subbox.style.left = (e.clientX - parentRect.left - offsetX) + "px";
      featureSettings.subtitlestyle.position[0] = subbox.style.left;
      subbox.style.bottom = (parentRect.bottom - e.clientY - offsetY) + "px";
      featureSettings.subtitlestyle.position[1] = subbox.style.bottom;
    }
  };

  return { subbox, onMouseDown, onMouseUp, onMouseMove };
}