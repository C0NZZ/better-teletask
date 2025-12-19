(async function() {
  const { removeResizeLimit, doubleclickHandler, keydownHandler, subtitleDragHandler, mediasessionHandler } = await import(browser.runtime.getURL('tweaks.js'));
  const player = document.querySelector('video-player');
  if (!player) {
    console.warn("[btt-tweaks] video player not found, couldn't apply tweaks")
    return;
  }
  const { featureSettings } = await browser.storage.local.get('featureSettings');

  removeResizeLimit(featureSettings);

  document.addEventListener('dblclick', doubleclickHandler(featureSettings, player), true);

  document.addEventListener('keydown', keydownHandler(featureSettings, player));

  if ('mediaSession' in navigator && navigator.mediaSession?.setActionHandler) {
    try {
      const mediaHandler = mediasessionHandler(featureSettings, player);
      navigator.mediaSession.setActionHandler('play', mediaHandler);
      navigator.mediaSession.setActionHandler('pause', mediaHandler);
    } catch (err) {
      console.warn('[btt-tweaks] failed to register mediaSession handlers', err);
    }
  }

  const subtitleDragHandlers = subtitleDragHandler(featureSettings, player);
  if (subtitleDragHandlers) {
    subtitleDragHandlers.subbox.addEventListener('mousedown', subtitleDragHandlers.onMouseDown);
    document.addEventListener('mouseup', subtitleDragHandlers.onMouseUp);
    document.addEventListener('mousemove', subtitleDragHandlers.onMouseMove);
  }

  console.info('[btt-tweaks] tweaks applied successfully');
})();