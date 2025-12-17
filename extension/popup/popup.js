document.addEventListener('DOMContentLoaded', async () => {
  {
    const input = document.getElementById('apikeyInput');
    const statusDiv = document.getElementById('apikeyStatus');
    const statusText = document.getElementById('apikeyStatusText');
    const statusSym = document.getElementById('apikeyStatusIcon').querySelector('path');
    const saveBtn = document.getElementById('apikeySave');
    const deleteBtn = document.getElementById('apikeyDelete');
    const toggleBtn = document.getElementById('apikeyToggle');
    const details = document.getElementById('apikey').querySelector('details')

    const { apiKey } = await browser.storage.local.get('apiKey');
    if (apiKey) {
      input.value = apiKey;
      input.type = "password";
      statusDiv.style.color = "var(--success)";
      statusText.textContent = "API key saved.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "visible";
    } else {details.open = true}

    toggleBtn.addEventListener('click', () => {
      if (input.type === "password") {
        input.type = "text";
        toggleBtn.querySelector('line').style.visibility = "visible";
      } else {
        input.type = "password";
        toggleBtn.querySelector('line').style.visibility = "hidden";
      }
    });

    saveBtn.addEventListener('click', async () => {
      const apiKey = input.value.trim();
      if (!apiKey) {
        statusDiv.style.color = "var(--error)";
        statusText.textContent = "No key entered.";
        statusSym.setAttribute("d", "M16 16l16 16M32 16l-16 16");
        return;
      }
      await browser.storage.local.set({ apiKey });
      input.type = "password";
      statusDiv.style.color = "var(--success)";
      statusText.textContent = "API key saved.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "visible";
      toggleBtn.querySelector('line').style.visibility = "hidden";
    });

    deleteBtn.addEventListener('click', async () => {
      await browser.storage.local.remove('apiKey');
      input.value = "";
      input.type = "text";
      statusDiv.style.color = "var(--success)";
      statusText.textContent = "API key deleted.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "hidden";
      toggleBtn.querySelector('line').style.visibility = "visible";
    });
  }
  {
    const subtitles = document.getElementById('featuresSubtitles');
    const doubleclick = document.getElementById('featuresDoubleclick');
    const noresizelimit = document.getElementById('featuresNoresizelimit')
    const kplay = document.getElementById('featuresKplay');
    const resizesubs = document.getElementById('featuresResizesubs');
    const movesubs = document.getElementById('featuresMovesubs');
    const saveBtn = document.getElementById('featuresSave');
    const reloadBtn = document.getElementById('featuresReload');
    const statusDiv = document.getElementById('featuresStatus');
    const { featureSettings } = await browser.storage.local.get('featureSettings');
    
    if (featureSettings) {
      for (const [key, value] of Object.entries(featureSettings)) {
        const element = document.getElementById(`features${key.charAt(0).toUpperCase() + key.slice(1)}`);
        if (element) {
          element.checked = value;
        }
      }
    }

    saveBtn.addEventListener('click', async () => {
      const featureSettings = {
        subtitles: subtitles.checked,
        doubleclick: doubleclick.checked,
        noresizelimit: noresizelimit.checked,
        kplay: kplay.checked,
        resizesubs: resizesubs.checked,
        movesubs: movesubs.checked,
      };
      await browser.storage.local.set({ featureSettings });
      statusDiv.style.visibility = "visible";
    });
    
    reloadBtn.addEventListener('click', async (e) => {
      const tabs = await browser.tabs.query({ active: true, currentWindow: true });
      if (tabs[0].url.startsWith("https://www.tele-task.de/lecture/video/")) await browser.tabs.reload(tabs[0].id);
    });
  }
});