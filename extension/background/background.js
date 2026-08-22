const HOST = "it.gianlucamazza.pagouse";
const JARVIS_GROUP = "jarvis";
const JARVIS_COLOR = "green";
const BLOCKED = new Set([
  "chrome:",
  "chrome-extension:",
  "chrome-search:",
  "chrome-untrusted:",
  "about:",
  "file:",
  "devtools:",
  "data:",
  "javascript:",
  "view-source:",
  "edge:",
  "brave:",
]);

let port = null;

function hasAllUrls() {
  // Promise-only: passing a callback AND using the returned Promise makes
  // Chromium reject an extra promise and log it at background.js:0.
  return chrome.permissions.contains({ origins: ["<all_urls>"] });
}

function captureVisible(windowId) {
  return chrome.tabs.captureVisibleTab(windowId, { format: "jpeg", quality: 80 });
}

function originOf(url) {
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

function schemeBlocked(url) {
  try {
    const scheme = new URL(url).protocol;
    if (BLOCKED.has(scheme)) return true;
    return scheme !== "http:" && scheme !== "https:";
  } catch {
    return true;
  }
}

function connect() {
  if (port) {
    try {
      port.disconnect();
    } catch {
      /* already gone */
    }
  }
  try {
    port = chrome.runtime.connectNative(HOST);
  } catch (err) {
    port = null;
    return;
  }
  port.onMessage.addListener((msg) => {
    handle(msg)
      .catch((err) => ({
        ok: false,
        error: err && err.code ? String(err.code) : "ipc_failed",
        message: String(err && err.message ? err.message : err),
      }))
      .then((reply) => {
        if (port) port.postMessage({ id: msg.id, ...reply });
      });
  });
  port.onDisconnect.addListener(() => {
    port = null;
    let delay = 200;
    const retry = () => {
      if (port) return;
      connect();
      if (!port) {
        delay = Math.min(delay * 2, 4000);
        setTimeout(retry, delay);
      }
    };
    setTimeout(retry, delay);
  });
}

async function ensureAx(tabId, frameId) {
  const target =
    frameId != null ? { tabId, frameIds: [frameId] } : { tabId, allFrames: true };
  await execScript(target, { files: ["content/ax.js"] });
}

// Chromium refuses injection on some pages (Web Store gallery, privileged
// origins) or when site access is restricted. Those are policy outcomes,
// not transport faults: tag them so the reply carries a stable code.
function classifyInject(err) {
  const text = String(err && err.message ? err.message : err);
  if (
    /cannot be scripted|cannot access contents of|has not been invoked/i.test(
      text,
    )
  ) {
    const tagged = new Error(text);
    tagged.code = "restricted_page";
    throw tagged;
  }
  throw err;
}

async function execScript(target, options) {
  try {
    return await chrome.scripting.executeScript({
      target,
      world: "ISOLATED",
      ...options,
    });
  } catch (err) {
    return classifyInject(err);
  }
}

function parseRef(ref) {
  const tagged = /^ref_f(\d+)_(\d+)$/.exec(ref || "");
  if (tagged) return { frameId: Number(tagged[1]), local: `ref_f${tagged[1]}_${tagged[2]}` };
  return { frameId: null, local: ref };
}

async function pickTab(tabId) {
  if (tabId != null) {
    try {
      return await chrome.tabs.get(tabId);
    } catch {
      return null;
    }
  }
  const [active] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (active && !schemeBlocked(active.url || "")) return active;
  const all = await chrome.tabs.query({ lastFocusedWindow: true });
  return all.find((t) => !schemeBlocked(t.url || "")) || null;
}

// Origins Chromium refuses to script regardless of host permissions.
const UNSCRIPTABLE = [
  "https://chrome.google.com/webstore",
  "https://chromewebstore.google.com",
];

function scriptable(url) {
  return !UNSCRIPTABLE.some((prefix) => (url || "").startsWith(prefix));
}

async function listTabs() {
  const raw = await chrome.tabs.query({});
  const tabs = raw
    .filter((t) => t.url && !schemeBlocked(t.url))
    .map((t) => ({
      id: t.id,
      url: t.url,
      title: t.title || "",
      active: Boolean(t.active),
      origin: originOf(t.url),
      scriptable: scriptable(t.url),
    }));
  const active = tabs.find((t) => t.active)?.id ?? tabs[0]?.id ?? null;
  return { ok: true, op: "tabs", tabs, active };
}

async function runInTab(tab, func, args, frameId) {
  await ensureAx(tab.id, frameId);
  const target =
    frameId != null ? { tabId: tab.id, frameIds: [frameId] } : { tabId: tab.id };
  const [inj] = await execScript(target, { func, args });
  return inj && inj.result;
}

async function runByRef(tab, ref, func) {
  const parsed = parseRef(ref);
  return runInTab(tab, func, [parsed.local], parsed.frameId);
}

async function ensureJarvisGroup(tabId) {
  // Tabs pagouse drives sit in a green "jarvis" group, not Claude's.
  try {
    const tab = await chrome.tabs.get(tabId);
    if (tab.groupId !== chrome.tabGroups.TAB_GROUP_ID_NONE) {
      try {
        const current = await chrome.tabGroups.get(tab.groupId);
        if (current.title === JARVIS_GROUP) return tab.groupId;
      } catch {
        /* group vanished */
      }
    }
    const found = await chrome.tabGroups.query({
      windowId: tab.windowId,
      title: JARVIS_GROUP,
    });
    const groupId =
      found.length > 0
        ? await chrome.tabs.group({ tabIds: [tabId], groupId: found[0].id })
        : await chrome.tabs.group({ tabIds: [tabId] });
    await chrome.tabGroups.update(groupId, {
      title: JARVIS_GROUP,
      color: JARVIS_COLOR,
      collapsed: false,
    });
    return groupId;
  } catch {
    return null;
  }
}

function originChanged(tab, expected) {
  if (!expected) return null;
  const now = originOf(tab.url || "");
  const want = expected.includes("://") ? originOf(expected) || expected : expected;
  if (now && want && now !== want) {
    return {
      ok: false,
      error: "origin_changed",
      message: `tab origin is ${now}, expected ${want}`,
    };
  }
  return null;
}

async function handle(msg) {
  const op = msg.op;
  if (op === "ping" || op === "hello") {
    return {
      ok: true,
      op,
      version: chrome.runtime.getManifest().version,
      all_urls: await hasAllUrls(),
    };
  }
  if (op === "tabs") return listTabs();

  const tab = await pickTab(msg.tab_id);
  if (!tab || tab.id == null) return { ok: false, error: "no_tab", message: "no usable tab" };
  if (schemeBlocked(tab.url || "") && op !== "navigate" && op !== "tab_open") {
    return { ok: false, error: "denied", message: `refusing ${originOf(tab.url || "")}` };
  }

  if (op === "snapshot") {
    const opts = {
      filter: msg.filter || "interactive",
      depth: msg.depth || 15,
      maxChars: msg.max_chars || 50000,
    };
    await ensureAx(tab.id);
    const probes = await execScript(
      { tabId: tab.id, allFrames: true },
      { func: () => ({ href: location.href, title: document.title }) },
    );
    const chunks = [];
    const frameErrors = [];
    let refs = 0;
    let filter = opts.filter;
    for (const probe of probes || []) {
      if (probe.frameId == null) continue;
      const fid = probe.frameId;
      let result = null;
      try {
        const [inj] = await execScript(
          { tabId: tab.id, frameIds: [fid] },
          {
            func: (o) => globalThis.__pagouse.snapshot(o),
            args: [{ ...opts, refPrefix: `f${fid}_` }],
          },
        );
        result = inj && inj.result;
        if (result && result.ok === false) result = null;
      } catch (err) {
        // A restricted sub-frame must not void the snapshot; a failed
        // main frame is the whole answer.
        if (fid === 0) throw err;
        frameErrors.push({ frame: fid, reason: String(err.message || err) });
        continue;
      }
      filter = result.filter || filter;
      refs += result.refs || 0;
      const href = result.url || (probe.result && probe.result.href) || "";
      if (fid === 0) chunks.unshift(result.tree || "");
      else chunks.push(`iframe ${href}\n${result.tree || ""}`);
    }
    if (!chunks.length) return { ok: false, error: "ipc_failed", message: "snapshot failed" };
    const reply = {
      ok: true,
      op: "snapshot",
      tab_id: tab.id,
      url: tab.url,
      title: tab.title,
      tree: chunks.join(""),
      refs,
      filter,
    };
    if (frameErrors.length) reply.frame_errors = frameErrors;
    return reply;
  }

  if (op === "shot") {
    try {
      await ensureJarvisGroup(tab.id);
      const granted = await hasAllUrls();
      if (!granted) {
        return {
          ok: false,
          error: "denied",
          message:
            "shot needs Site access = On all sites (chrome://extensions → pagouse → Details), or click Grant in the popup",
        };
      }
      await chrome.tabs.update(tab.id, { active: true });
      const visible = await chrome.tabs.get(tab.id);
      if (schemeBlocked(visible.url || "")) {
        return {
          ok: false,
          error: "denied",
          message: `shot cannot capture ${originOf(visible.url || "") || "this tab"}`,
        };
      }
      try {
        await chrome.windows.update(tab.windowId, { focused: true });
      } catch {
        /* focusing can fail on some Wayland seats; capture may still work */
      }
      const dataUrl = await captureVisible(tab.windowId);
      return {
        ok: true,
        op: "shot",
        tab_id: tab.id,
        data_url: dataUrl,
        width: tab.width || 0,
        height: tab.height || 0,
      };
    } catch (err) {
      const text = String(err && err.message ? err.message : err);
      const code = /activeTab|not in effect|not authorized/i.test(text)
        ? "denied"
        : "ipc_failed";
      return { ok: false, error: code, message: `shot: ${text}` };
    }
  }

  const shifted = originChanged(tab, msg.expected_origin);
  if (shifted) return shifted;

  if (op === "scroll") {
    if (!msg.ref) return { ok: false, error: "bad_arg", message: "ref is required" };
    await ensureJarvisGroup(tab.id);
    const result = await runByRef(tab, msg.ref, (ref) => globalThis.__pagouse.scrollTo(ref));
    return result
      ? { ...result, op: "scroll", tab_id: tab.id }
      : { ok: false, error: "ipc_failed", message: "scroll failed" };
  }

  if (op === "click") {
    if (!msg.ref) return { ok: false, error: "bad_arg", message: "ref is required" };
    await ensureJarvisGroup(tab.id);
    const result = await runByRef(tab, msg.ref, (ref) => globalThis.__pagouse.click(ref));
    return result
      ? { ...result, op: "click", tab_id: tab.id }
      : { ok: false, error: "ipc_failed", message: "click failed" };
  }

  if (op === "fill") {
    if (!msg.ref) return { ok: false, error: "bad_arg", message: "ref is required" };
    await ensureJarvisGroup(tab.id);
    const parsed = parseRef(msg.ref);
    const result = await runInTab(
      tab,
      (ref, value) => globalThis.__pagouse.fill(ref, value),
      [parsed.local, msg.value],
      parsed.frameId,
    );
    return result
      ? { ...result, op: "fill", tab_id: tab.id }
      : { ok: false, error: "ipc_failed", message: "fill failed" };
  }

  if (op === "type") {
    await ensureJarvisGroup(tab.id);
    const result = await runInTab(tab, (text) => globalThis.__pagouse.typeText(text), [
      msg.text || "",
    ]);
    return result
      ? { ...result, op: "type", tab_id: tab.id }
      : { ok: false, error: "ipc_failed", message: "type failed" };
  }

  if (op === "key") {
    await ensureJarvisGroup(tab.id);
    const result = await runInTab(tab, (combo) => globalThis.__pagouse.key(combo), [
      msg.combo || "",
    ]);
    return result
      ? { ...result, op: "key", tab_id: tab.id }
      : { ok: false, error: "ipc_failed", message: "key failed" };
  }

  if (op === "navigate") {
    await ensureJarvisGroup(tab.id);
    const url = msg.url;
    if (url === "back") {
      await chrome.tabs.goBack(tab.id);
      return { ok: true, op: "navigate", tab_id: tab.id, url: "back" };
    }
    if (url === "forward") {
      await chrome.tabs.goForward(tab.id);
      return { ok: true, op: "navigate", tab_id: tab.id, url: "forward" };
    }
    if (schemeBlocked(url)) {
      return { ok: false, error: "denied", message: `refusing ${url}` };
    }
    await chrome.tabs.update(tab.id, { url });
    return { ok: true, op: "navigate", tab_id: tab.id, url };
  }

  if (op === "tab_open") {
    const url = msg.url || "about:blank";
    if (url !== "about:blank" && schemeBlocked(url)) {
      return { ok: false, error: "denied", message: `refusing ${url}` };
    }
    const created = await chrome.tabs.create({ url });
    if (created.id != null) await ensureJarvisGroup(created.id);
    return { ok: true, op: "tab_open", tab_id: created.id, url: created.url || url };
  }

  if (op === "tab_focus") {
    await ensureJarvisGroup(tab.id);
    await chrome.tabs.update(tab.id, { active: true });
    return { ok: true, op: "tab_focus", tab_id: tab.id };
  }

  if (op === "wait_ref") {
    const ref = msg.ref || "";
    const timeoutMs = msg.timeout_ms || 5000;
    const pollInterval = 150;
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      try {
        const result = await runByRef(tab, ref, (r) => globalThis.__pagouse.lookup(r) ? { ok: true } : { ok: false });
        if (result && result.ok) {
          return { ok: true, op: "wait_ref", tab_id: tab.id, ref, matched: true };
        }
      } catch {
        /* ref not found yet, keep polling */
      }
      await new Promise((r) => setTimeout(r, pollInterval));
    }
    return { ok: false, error: "wait_timeout", message: `ref ${ref} not found after ${timeoutMs}ms` };
  }

  return { ok: false, error: "bad_arg", message: `unknown op ${op}` };
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.op === "status") {
    sendResponse({ ok: Boolean(port) });
    return true;
  }
  return false;
});

chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();
