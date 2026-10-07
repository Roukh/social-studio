// Run inside the sandbox (qa.py: engine.bwrap_argv(..., network=False)), never given network access: it loads
// `comp/index.html` in the engine's own pinned headless Chrome (puppeteer-core, already in the engine's
// node_modules — nothing is installed here) and reports what a viewer would see at each requested time.
//
// HyperFrames seeks a built frame the same way at render time (node_modules/hyperframes/dist/chunk-VW5OMJNG.js,
// `seekPageTimeline`/`prepareFrameForCapture`): it calls `window.__hf.seek(t, opts)` on a GSAP timeline, waits for
// `document.fonts.ready` and any pending composite work, then captures. We mirror that directly against the GSAP
// timeline the composition registers at `window.__timelines["main"]` (runner._scaffold's contract), since loading
// the page outside `hyperframes render` never injects the full `window.__hf` player: seek with suppressEvents so
// GSAP callbacks do not fire out of order, then wait for fonts and one extra animation frame so layout is final.
//
// Usage: node qa-probe.mjs <config.json >result.json
//   config: {html, chrome, engineRoot, width, height, times: [seconds, ...]}
//   result: {times: [{t, nodes: [{text, box, font_size, font_weight, font_family, color, opacity, bg}]}]}

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function loadPuppeteer(engineRoot) {
  const entry = path.join(engineRoot, "node_modules", "puppeteer-core", "lib", "puppeteer", "puppeteer-core.js");
  const mod = await import(pathToFileURL(entry).href);
  return mod.default;
}

// Runs inside the page. Kept as one function (not split across evaluate calls) so it serialises cleanly.
function extractVisibleText(width, height) {
  const out = [];
  const skipTags = new Set(["SCRIPT", "STYLE", "TITLE", "NOSCRIPT", "TEMPLATE", "HEAD"]);
  const genericFamilies = new Set(["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "emoji", "math", "fangsong"]);

  function parseColor(value) {
    const m = /rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?\)/.exec(value || "");
    if (!m) return null;
    return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])];
  }

  function effectiveOpacity(el) {
    let node = el, opacity = 1;
    while (node && node.nodeType === 1) {
      const v = parseFloat(getComputedStyle(node).opacity);
      if (!Number.isNaN(v)) opacity *= v;
      node = node.parentElement;
    }
    return opacity;
  }

  // First non-transparent background walking up from the element itself. A background-image (including a
  // CSS gradient, which computes as one) makes the real background unknowable from here, so that stops the
  // walk and reports `null`: the caller then skips contrast for this element rather than risk a false finding.
  function effectiveBackground(el) {
    let node = el;
    while (node && node.nodeType === 1) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== "none") return null;
      const bg = parseColor(cs.backgroundColor);
      if (bg && bg[3] > 0.001) return bg;
      node = node.parentElement;
    }
    return null;
  }

  // Where the element's own text is drawn, not its box: a block heading's box spans the full width, its words do
  // not. Range rects are in viewport pixels after transforms, the way the frame shows them.
  function textRect(el) {
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    for (const n of el.childNodes) {
      if (n.nodeType !== 3 || !n.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const q of range.getClientRects()) {
        if (q.width <= 0 || q.height <= 0) continue;
        l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom);
      }
    }
    return l === Infinity ? { left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0 }
      : { left: l, top: t, right: r, bottom: b, width: r - l, height: b - t };
  }

  function isVisible(el, cs, rect) {
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    if (rect.width <= 0 || rect.height <= 0) return false;
    if (rect.right <= 0 || rect.bottom <= 0 || rect.left >= width || rect.top >= height) return false;
    return effectiveOpacity(el) > 0.01;
  }

  // Reported elements, by document order. An ancestor is always visited first, so `parents` can list the reported
  // elements that contain this one: the overlap gate never counts a line against a word inside it.
  const ids = new Map();
  document.querySelectorAll("*").forEach((el) => {
    if (skipTags.has(el.tagName)) return;
    const hasDirectText = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim().length > 0);
    if (!hasDirectText) return;
    const cs = getComputedStyle(el);
    const rect = textRect(el);
    if (!isVisible(el, cs, rect)) return;
    const family = cs.fontFamily.split(",")[0].trim().replace(/^["']|["']$/g, "");
    const parents = [];
    for (let a = el.parentElement; a; a = a.parentElement) if (ids.has(a)) parents.push(ids.get(a));
    ids.set(el, out.length);
    out.push({
      id: out.length,
      parents,
      text: el.textContent.trim().slice(0, 200),
      box: { x: rect.left, y: rect.top, w: rect.width, h: rect.height },
      font_size: parseFloat(cs.fontSize) || 0,
      font_weight: parseInt(cs.fontWeight, 10) || 400,
      font_family: family,
      font_generic: genericFamilies.has(family.toLowerCase()),
      color: parseColor(cs.color) || [0, 0, 0, 1],
      opacity: effectiveOpacity(el),
      bg: effectiveBackground(el),
    });
  });
  return out;
}

async function main() {
  const config = JSON.parse(fs.readFileSync(process.argv[2] ?? 0, "utf8"));
  const { html, chrome, engineRoot, width, height, times, userDataDir } = config;
  const puppeteer = await loadPuppeteer(engineRoot);
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: chrome,
    // Chrome's own profile dir, not the OS temp dir: inside the jail only `work` (which this lives under)
    // is writable, and the OS default of /tmp is not guaranteed to be.
    userDataDir,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
      "--force-color-profile=srgb"],
    defaultViewport: { width, height },
  });
  try {
    const page = await browser.newPage();
    // The real render environment defines `window.__timelines` before the composition's own script runs
    // (hyperframes/dist chunk-TH4APNRP.js); the scaffold's script assumes it exists, so we must too.
    await page.evaluateOnNewDocument(() => {
      window.__timelines = window.__timelines || {};
    });
    await page.goto(pathToFileURL(html).href, { waitUntil: "load" });
    await page.waitForFunction(() => !!(window.__timelines && window.__timelines.main), { timeout: 15000 });
    const result = { times: [] };
    for (const t of times) {
      await page.evaluate((tt) => {
        window.__timelines.main.seek(tt, true); // suppressEvents: mirrors the render's own seek
        // The engine's player shows a timed element only inside its [data-start, data-start + data-duration) window
        // and its timed ancestors' (hyperframes/dist, `k.style.visibility = W ? "visible" : "hidden"`). Without
        // the player, a finished shot would stay on screen here and read as overlapping the next one.
        const active = (el) => {
          for (let n = el; n; n = n.parentElement ? n.parentElement.closest("[data-start]") : null) {
            if (n.hasAttribute("data-hidden")) return false;
            const s = parseFloat(n.getAttribute("data-start")), d = parseFloat(n.getAttribute("data-duration"));
            if (!Number.isNaN(s) && tt < s) return false;
            if (!Number.isNaN(s) && !Number.isNaN(d) && tt >= s + d) return false;
          }
          return true;
        };
        document.querySelectorAll("[data-start]").forEach((el) => {
          el.style.visibility = active(el) ? "visible" : "hidden";
        });
      }, t);
      await page.evaluate(() => document.fonts.ready);
      // One extra round trip through the event loop so a just-applied style has actually painted/laid out.
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
      const nodes = await page.evaluate(extractVisibleText, width, height);
      result.times.push({ t, nodes });
    }
    process.stdout.write(JSON.stringify(result));
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  process.stderr.write(String((e && e.stack) || e) + "\n");
  process.exit(1);
});
