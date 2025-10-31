document.addEventListener('DOMContentLoaded', async () => {
  const apiKeyInput = document.getElementById('apiKey');
  const statusEl = document.getElementById('status');
  const saveBtn = document.getElementById('save');

  const { apiKey } = await browser.storage.local.get('apiKey');
  if (apiKey) {
    // apiKeyInput.value = apiKey;
    // apiKeyInput.type = 'password';
    statusEl.textContent = "API key saved";
  }

  saveBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
      await browser.storage.local.remove('apiKey');
      statusEl.textContent = "Error: No key entered.";
      return;
    }

    await browser.storage.local.set({ apiKey });
    statusEl.textContent = "API key saved";
  });
});
