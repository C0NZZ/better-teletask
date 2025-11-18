document.addEventListener('DOMContentLoaded', async () => {
  const apiKeyInput = document.getElementById('apiKey');
  const statusDiv = document.getElementById('status');
  const statusText = document.getElementById('statust');
  const statusSym = document.getElementById('statuss').querySelector('path');
  const saveBtn = document.getElementById('save');
  const deleteBtn = document.getElementById('statusb');

  const { apiKey } = await browser.storage.local.get('apiKey');
  if (apiKey) {
    apiKeyInput.value = apiKey;
    // apiKeyInput.type = 'password';
    statusDiv.style.color = "#77b379ff";
    statusText.textContent = "API key saved.";
    statusSym.setAttribute("d", "M14 25l6 6 14-14");
    deleteBtn.style.visibility = "visible";
  }

  saveBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
      statusDiv.style.color = "#f6a09aff";
      statusText.textContent = "No key entered.";
      statusSym.setAttribute("d", "M16 16l16 16M32 16l-16 16");
      return;
    }
    await browser.storage.local.set({ apiKey });
  });

  deleteBtn.addEventListener('click', async () => {
    if (apiKey) {
      await browser.storage.local.remove('apiKey');
      apiKeyInput.value = "";
      statusDiv.style.color = "#77b379ff";
      statusText.textContent = "API key deleted.";
      statusSym.setAttribute("d", "M14 25l6 6 14-14");
      deleteBtn.style.visibility = "hidden";
    }
  });
});