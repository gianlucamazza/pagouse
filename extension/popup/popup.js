async function main() {
  const status = document.getElementById("status");
  const permEl = document.getElementById("perm");
  const grantBtn = document.getElementById("grant");
  const tabEl = document.getElementById("tab");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) tabEl.textContent = tab.title || tab.url || "";

  const granted = await chrome.permissions.contains({ origins: ["<all_urls>"] });
  if (granted) {
    permEl.textContent = "site access: all sites";
  } else {
    permEl.textContent = "site access: withheld — shot will fail";
    grantBtn.hidden = false;
    grantBtn.addEventListener("click", async () => {
      const ok = await chrome.permissions.request({ origins: ["<all_urls>"] });
      permEl.textContent = ok ? "site access: all sites" : "grant dismissed";
      grantBtn.hidden = ok;
    });
  }

  try {
    const ping = await chrome.runtime.sendMessage({ op: "status" });
    if (ping && ping.ok) {
      status.textContent = "daemon connected";
      status.className = "ok";
      return;
    }
  } catch {
    /* service worker answers below */
  }
  status.textContent = "native host not connected — run install/install-host.sh";
  status.className = "fail";
}

main();
