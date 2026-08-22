// Accessibility walker + WeakRef map. Isolated world; persists per document.
// The Python formatter in pagouse.ax formats the same node shape.

(() => {
  const MAX_NAME = 80;
  const INTERACTIVE_ROLES = new Set([
    "button",
    "link",
    "textbox",
    "searchbox",
    "combobox",
    "checkbox",
    "radio",
    "switch",
    "slider",
    "spinbutton",
    "listbox",
    "option",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "tab",
    "treeitem",
    "textbox",
  ]);

  const TAG_ROLE = {
    A: "link",
    BUTTON: "button",
    NAV: "navigation",
    MAIN: "main",
    HEADER: "banner",
    FOOTER: "contentinfo",
    FORM: "form",
    IMG: "image",
    TABLE: "table",
    H1: "heading",
    H2: "heading",
    H3: "heading",
    H4: "heading",
    H5: "heading",
    H6: "heading",
    TEXTAREA: "textbox",
    SELECT: "combobox",
    SUMMARY: "button",
    LABEL: "label",
    LI: "listitem",
    UL: "list",
    OL: "list",
  };

  function inputRole(el) {
    const type = (el.type || "text").toLowerCase();
    if (type === "hidden") return null;
    if (type === "checkbox") return "checkbox";
    if (type === "radio") return "radio";
    if (type === "range") return "slider";
    if (type === "number") return "spinbutton";
    if (type === "submit" || type === "reset" || type === "button" || type === "file") {
      return "button";
    }
    if (type === "search") return "searchbox";
    return "textbox";
  }

  function roleOf(el) {
    const explicit = el.getAttribute("role");
    if (explicit) return explicit;
    if (el instanceof HTMLInputElement) return inputRole(el);
    if (el.isContentEditable) return "textbox";
    return TAG_ROLE[el.tagName] || null;
  }

  function isHidden(el) {
    if (el.hasAttribute("hidden") || el.getAttribute("aria-hidden") === "true") return true;
    if (el instanceof HTMLInputElement && el.type === "hidden") return true;
    const style = window.getComputedStyle(el);
    return style.display === "none" || style.visibility === "hidden" || style.opacity === "0";
  }

  function labelFor(el) {
    if (el.id) {
      const lab = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lab) return lab.textContent || "";
    }
    const parent = el.closest("label");
    if (parent) return parent.textContent || "";
    return "";
  }

  function accessibleName(el) {
    const labelled = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby");
    if (el.getAttribute("aria-label")) return el.getAttribute("aria-label");
    if (el.getAttribute("aria-labelledby")) {
      const parts = el
        .getAttribute("aria-labelledby")
        .split(/\s+/)
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((n) => n.textContent || "");
      if (parts.length) return parts.join(" ");
    }
    const lab = labelFor(el);
    if (lab.trim()) return lab;
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      if (el.placeholder) return el.placeholder;
    }
    if (el instanceof HTMLImageElement && el.alt) return el.alt;
    if (el.getAttribute("title")) return el.getAttribute("title");
    const text = (el.innerText || el.textContent || "").trim();
    return text;
  }

  function clip(name) {
    const collapsed = String(name || "").replace(/\s+/g, " ").trim();
    if (collapsed.length <= MAX_NAME) return collapsed;
    return collapsed.slice(0, MAX_NAME - 1) + "…";
  }

  function isSecret(el) {
    if (!(el instanceof HTMLInputElement)) return false;
    const type = (el.type || "").toLowerCase();
    if (type === "password") return true;
    const ac = (el.autocomplete || "").toLowerCase();
    return ac.includes("password") || ac.includes("cc-") || ac.includes("one-time-code");
  }

  function isInteractive(el, role) {
    if (el.tabIndex >= 0 && el.tabIndex !== 0 && el.hasAttribute("tabindex")) {
      /* keep going */
    }
    if (INTERACTIVE_ROLES.has(role)) return true;
    if (el instanceof HTMLInputElement) return el.type !== "hidden";
    if (el instanceof HTMLButtonElement || el instanceof HTMLSelectElement) return true;
    if (el instanceof HTMLTextAreaElement) return true;
    if (el instanceof HTMLAnchorElement && el.hasAttribute("href")) return true;
    if (el.isContentEditable) return true;
    if (el.onclick || el.getAttribute("onclick")) return true;
    return false;
  }

  function store(el) {
    if (!globalThis.__pagouseRefs) {
      globalThis.__pagouseRefs = new Map();
      globalThis.__pagouseNext = 1;
    }
    for (const [ref, wr] of globalThis.__pagouseRefs) {
      if (wr.deref() === el) return ref;
    }
    // Purge dead refs to avoid unbounded Map growth on SPA navigation.
    for (const [ref, wr] of globalThis.__pagouseRefs) {
      if (!wr.deref()) globalThis.__pagouseRefs.delete(ref);
    }
    const prefix = globalThis.__pagousePrefix || "";
    const ref = `ref_${prefix}${globalThis.__pagouseNext++}`;
    globalThis.__pagouseRefs.set(ref, new WeakRef(el));
    return ref;
  }

  function lookup(ref) {
    const wr = globalThis.__pagouseRefs && globalThis.__pagouseRefs.get(ref);
    return wr ? wr.deref() : undefined;
  }

  function nodeOf(el, role) {
    const node = {
      role,
      name: clip(accessibleName(el)),
      ref: store(el),
    };
    if (el instanceof HTMLAnchorElement && el.getAttribute("href")) {
      node.href = el.getAttribute("href");
    }
    if (el instanceof HTMLInputElement) {
      node.type = el.type;
      if (el.placeholder) node.placeholder = el.placeholder;
      if (el.type === "checkbox" || el.type === "radio") node.checked = el.checked;
      if (isSecret(el)) node.redacted = true;
      else if (el.value && el.type !== "password") node.value = clip(el.value);
    }
    if (el instanceof HTMLSelectElement) {
      node.children = [...el.options].map((opt) => ({
        role: "option",
        name: clip(opt.textContent || opt.value),
        ref: store(opt),
        value: opt.value,
        ...(opt.selected ? { checked: true } : {}),
      }));
    }
    return node;
  }

  function walk(el, depth, filter, acc) {
    if (depth < 0 || !(el instanceof Element) || isHidden(el)) return;
    const role = roleOf(el);
    const interactive = role ? isInteractive(el, role) : false;
    const keep = filter === "all" ? Boolean(role) : interactive;
    let nextAcc = acc;
    if (keep && role) {
      const node = nodeOf(el, role);
      node.children = [];
      acc.children.push(node);
      nextAcc = node;
    }
    if (el instanceof HTMLSelectElement) return;
    for (const child of el.children) walk(child, depth - 1, filter, nextAcc);
  }

  function snapshot(opts) {
    globalThis.__pagousePrefix = (opts && opts.refPrefix) || "";
    const filter = (opts && opts.filter) || "interactive";
    const depth = opts && opts.depth != null ? opts.depth : 15;
    const maxChars = opts && opts.maxChars != null ? opts.maxChars : 50000;
    const root = {
      role: "RootWebArea",
      name: clip(document.title || ""),
      ref: store(document.documentElement),
      children: [],
    };
    walk(document.body || document.documentElement, depth, filter, root);
    const tree = formatTree(root);
    if (tree.length > maxChars) {
      return {
        ok: false,
        error: "bad_arg",
        message: `snapshot exceeded ${maxChars} characters; pass a smaller depth`,
      };
    }
    return {
      ok: true,
      tree,
      refs: countRefs(root),
      filter,
      url: location.href,
      title: document.title,
    };
  }

  function formatTree(node, indent) {
    indent = indent || 0;
    const bits = ["  ".repeat(indent) + node.role];
    if (node.name) bits.push(`"${node.name}"`);
    if (node.ref) bits.push(`[${node.ref}]`);
    const extras = [];
    if (node.href) extras.push(`href=${node.href}`);
    if (node.type) extras.push(`type=${node.type}`);
    if (node.placeholder) extras.push(`placeholder=${node.placeholder}`);
    if (node.redacted) extras.push("[redacted]");
    if (node.checked) extras.push("checked");
    if (node.value && !node.redacted) extras.push(`value=${node.value}`);
    if (extras.length) bits.push(extras.join(" "));
    const lines = [bits.join(" ")];
    for (const child of node.children || []) lines.push(formatTree(child, indent + 1));
    return indent === 0 ? lines.join("\n") + "\n" : lines.join("\n");
  }

  function countRefs(node) {
    let n = node.ref ? 1 : 0;
    for (const child of node.children || []) n += countRefs(child);
    return n;
  }

  function setNativeValue(el, value) {
    const proto =
      el instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
    const desc = Object.getOwnPropertyDescriptor(proto, "value");
    if (desc && desc.set) desc.set.call(el, value);
    else el.value = value;
  }

  function fire(el) {
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function scrollTo(ref) {
    const el = lookup(ref);
    if (!el) return { ok: false, error: "stale_ref", message: `${ref} is no longer in the document` };
    el.scrollIntoView({ block: "center", inline: "nearest" });
    return { ok: true, ref, url: location.href };
  }

  function click(ref) {
    const el = lookup(ref);
    if (!el) return { ok: false, error: "stale_ref", message: `${ref} is no longer in the document` };
    el.scrollIntoView({ block: "center", inline: "nearest" });
    el.click();
    return { ok: true, ref, url: location.href };
  }

  function fill(ref, value) {
    const el = lookup(ref);
    if (!el) return { ok: false, error: "stale_ref", message: `${ref} is no longer in the document` };
    el.scrollIntoView({ block: "center", inline: "nearest" });
    el.focus();
    if (el instanceof HTMLInputElement && (el.type === "checkbox" || el.type === "radio")) {
      const on = value === true || value === "true" || value === "1" || value === "on";
      el.checked = on;
    } else if (el instanceof HTMLSelectElement) {
      el.value = String(value);
    } else if (el.isContentEditable) {
      el.textContent = String(value);
    } else {
      setNativeValue(el, String(value));
    }
    fire(el);
    return { ok: true, ref, url: location.href };
  }

  function typeText(text) {
    const el = document.activeElement;
    if (!(el instanceof HTMLElement)) {
      return { ok: false, error: "bad_arg", message: "no focused element" };
    }
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      setNativeValue(el, (el.value || "") + text);
      fire(el);
    } else if (el.isContentEditable) {
      el.textContent = (el.textContent || "") + text;
      fire(el);
    } else {
      return { ok: false, error: "bad_arg", message: "focused element is not editable" };
    }
    return { ok: true, typed: String(text).length, url: location.href };
  }

  function key(combo) {
    const el = document.activeElement || document.body;
    const parts = String(combo)
      .split("+")
      .map((s) => s.trim())
      .filter(Boolean);
    const keyName = parts[parts.length - 1] || combo;
    const mods = new Set(parts.slice(0, -1).map((s) => s.toLowerCase()));
    const event = new KeyboardEvent("keydown", {
      key: keyName,
      bubbles: true,
      cancelable: true,
      ctrlKey: mods.has("ctrl") || mods.has("control"),
      altKey: mods.has("alt"),
      shiftKey: mods.has("shift"),
      metaKey: mods.has("meta") || mods.has("cmd"),
    });
    el.dispatchEvent(event);
    el.dispatchEvent(new KeyboardEvent("keyup", { key: keyName, bubbles: true }));
    if (keyName === "Enter" && el instanceof HTMLFormElement) el.submit();
    else if (keyName === "Enter" && el.form) el.form.requestSubmit?.();
    return { ok: true, combo, url: location.href };
  }

  globalThis.__pagouse = { snapshot, click, fill, typeText, key, scrollTo, lookup };
})();
