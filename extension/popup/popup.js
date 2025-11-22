document.addEventListener('DOMContentLoaded', async () => {
  {
    const input = document.getElementById('apikeyInput');
    const statusDiv = document.getElementById('apikeyStatus');
    const statusText = document.getElementById('apikeyStatusText');
    const statusSym = document.getElementById('apikeyStatusIcon').querySelector('path');
    const saveBtn = document.getElementById('apikeySave');
    const deleteBtn = document.getElementById('apikeyDelete');
    const toggleBtn = document.getElementById('apikeyToggle');

    const { apiKey } = await browser.storage.local.get('apiKey');
    if (apiKey) {
      input.value = apiKey;
      input.type = "password";
      statusDiv.style.color = "#77b379ff";
      statusText.textContent = "API key saved.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "visible";
      toggleBtn.style.visibility = "visible";
    }

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
        statusDiv.style.color = "#f6a09aff";
        statusText.textContent = "No key entered.";
        statusSym.setAttribute("d", "M16 16l16 16M32 16l-16 16");
        return;
      }
      await browser.storage.local.set({ apiKey });
      input.type = "password";
      statusDiv.style.color = "#77b379ff";
      statusText.textContent = "API key saved.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "visible";
      toggleBtn.style.visibility = "visible";
    });

    deleteBtn.addEventListener('click', async () => {
      await browser.storage.local.remove('apiKey');
      input.value = "";
      input.type = "text";
      statusDiv.style.color = "#77b379ff";
      statusText.textContent = "API key deleted.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "hidden";
      toggleBtn.style.visibility = "hidden"; toggleBtn.querySelector('line').style.visibility = "hidden";
    });
  }
  {
    const subtitles = document.getElementById('featuresSubtitles');
    const doubleclick = document.getElementById('featuresDoubleclick');
    const kplay = document.getElementById('featuresKplay');
    const saveBtn = document.getElementById('featuresSave');
    const reloadBtn = document.getElementById('featuresReload');
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
        kplay: kplay.checked
      };
      await browser.storage.local.set({ featureSettings });
    });
    
    reloadBtn.addEventListener('click', async (e) => {
      const tabs = await browser.tabs.query({ active: true, currentWindow: true });
      if (tabs[0].url.startsWith("https://www.tele-task.de/lecture/video/")) await browser.tabs.reload(tabs[0].id);
    });
  }
});