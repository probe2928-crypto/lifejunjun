// src/ (앱 화면) → www/ (Capacitor가 앱에 넣는 폴더). 여행·카드 데이터는 앱에 사본을 넣고, 실행 중엔 사이트의 최신본으로 바꿔 씀
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const APP = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(APP, "www");
fs.rmSync(OUT, { recursive: true, force: true });
fs.cpSync(path.join(APP, "src"), OUT, { recursive: true });
for (const f of ["trips", "cards"]) JSON.parse(fs.readFileSync(path.join(OUT, "data", f + ".json"), "utf8"));
const size = (d) => fs.readdirSync(d, { withFileTypes: true }).reduce((a, e) => a + (e.isDirectory() ? size(path.join(d, e.name)) : fs.statSync(path.join(d, e.name)).size), 0);
console.log(`www 준비 완료: ${(size(OUT) / 1e6).toFixed(1)}MB`);
