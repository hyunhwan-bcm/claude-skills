// Load a built viewer page in headless Chromium and check it before publishing.
// Usage: node check_viewer.js <folder> <page.html> [--shots <folder>]
// Reports: whether the first page drew and how fast, the page count, any page errors, and
// whether the layout scrolls sideways at phone width. Needs Playwright with Chromium
// (pre-installed in Claude Code cloud sessions; elsewhere: npm i playwright && npx playwright install chromium).
const http = require("http");
const fs = require("fs");
const path = require("path");

let chromium;
try { ({ chromium } = require("playwright")); }
catch (e) { console.error("Playwright is not installed; skip this check or install it."); process.exit(2); }

const [dir, pageName] = process.argv.slice(2);
const shotsAt = process.argv.indexOf("--shots");
const shots = shotsAt > 0 ? process.argv[shotsAt + 1] : null;
if (!dir || !pageName) { console.error("usage: node check_viewer.js <folder> <page.html> [--shots <folder>]"); process.exit(2); }

const types = { ".html": "text/html; charset=utf-8", ".pdf": "application/pdf" };
const server = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]));
  if (!p.startsWith(path.resolve(dir)) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});

server.listen(0, "127.0.0.1", async () => {
  const port = server.address().port;
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  const browser = await chromium.launch(proxy ? { proxy: { server: proxy, bypass: "127.0.0.1,localhost" } } : {});
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 860 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  const t0 = Date.now();
  await page.goto(`http://127.0.0.1:${port}/${pageName}`, { waitUntil: "load" });
  const drew = await page.waitForFunction(() => !document.getElementById("page").hidden, null, { timeout: 60000 })
    .then(() => true).catch(() => false);
  const seconds = (Date.now() - t0) / 1000;
  const count = await page.textContent("#count");
  const status = await page.evaluate(() => { const s = document.getElementById("status"); return s.hidden ? "" : s.textContent; });
  const sections = await page.$$eval(".chip", (c) => c.length);
  if (shots) { fs.mkdirSync(shots, { recursive: true }); await page.waitForTimeout(1500); await page.screenshot({ path: path.join(shots, "desktop.png") }); }
  await page.setViewportSize({ width: 400, height: 860 });
  await page.waitForTimeout(1200);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (shots) await page.screenshot({ path: path.join(shots, "phone.png") });
  await browser.close();
  server.close();
  const ok = drew && overflow <= 0 && !errors.length;
  console.log(JSON.stringify({ ok, first_page_drawn: drew, seconds, count, sections, status, phone_overflow_px: overflow, errors }, null, 1));
  process.exit(ok ? 0 : 1);
});
