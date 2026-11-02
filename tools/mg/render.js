// render.js — node render.js page.html out.mp4 dur [fps] [--bg footage.mp4] [--frames t1,t2,...]
// Without --bg: page is filmed as-is (JPEG 92). With --bg: page is filmed with a transparent background (PNG) and laid over the footage.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path'); const fs = require('fs');
const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
(async () => {
  const [page_, out, durS, fpsS] = process.argv.slice(2);
  const fps = +(fpsS && !fpsS.startsWith('--') ? fpsS : 30), dur = +durS;
  const bg = arg('--bg'), frames = arg('--frames');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(page_));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  const shot = () => bg ? page.screenshot({ type: 'png', omitBackground: true }) : page.screenshot({ type: 'jpeg', quality: 92 });
  if (frames) { // still frames for checking
    for (const t of frames.split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      const o = `${out}_${t.toFixed(2)}.jpg`;
      if (!bg) { fs.writeFileSync(o, await shot()); continue; }
      const p = o + '.png'; fs.writeFileSync(p, await shot());
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(t), '-i', bg, '-i', p, '-filter_complex', '[0:v][1:v]overlay', '-frames:v', '1', '-q:v', '3', o]);
      fs.unlinkSync(p);
    }
    await browser.close(); return;
  }
  const tmp = out.replace(/\.mp4$/, '.part.mp4');
  const enc = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), '-t', String(dur), tmp];
  const args = bg
    ? ['-y', '-loglevel', 'error', '-i', bg, '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-', '-filter_complex', '[0:v][1:v]overlay=shortest=1[o]', '-map', '[o]', ...enc]
    : ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', ...enc];
  const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(dur * fps);
  for (let f = 0; f < N; f++) {
    await page.evaluate(t => window.__seek(t), f / fps);
    const buf = await shot();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  await browser.close();
  if (code === 0) { fs.renameSync(tmp, out); console.log('ok', out, N, 'frames'); } else { console.error('ffmpeg failed', code); process.exit(1); }
})();
