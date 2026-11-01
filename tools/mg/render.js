// render.js — node render.js page.html out.mp4 dur [fps] [--frames t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'); const fs = require('fs');
(async () => {
  const [page_, out, durS, fpsS] = process.argv.slice(2);
  const fi = process.argv.indexOf('--frames');
  const fps = +(fpsS && !fpsS.startsWith('--') ? fpsS : 30), dur = +durS;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(page_));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  if (fi > 0) { // still frames for checking
    for (const t of process.argv[fi + 1].split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      await page.screenshot({ path: `${out}_${t.toFixed(2)}.jpg`, type: 'jpeg', quality: 90 });
    }
    await browser.close(); return;
  }
  const tmp = out.replace(/\.mp4$/, '.part.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(dur * fps);
  for (let f = 0; f < N; f++) {
    await page.evaluate(t => window.__seek(t), f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  await browser.close();
  if (code === 0) { fs.renameSync(tmp, out); console.log('ok', out, N, 'frames'); } else { console.error('ffmpeg failed', code); process.exit(1); }
})();
