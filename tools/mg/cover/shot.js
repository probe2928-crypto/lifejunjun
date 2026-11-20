const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
for(const f of process.argv.slice(2)){await p.goto('file://'+require('path').resolve(f));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(200);
await p.screenshot({path:f.replace('.html','.jpg'),type:'jpeg',quality:94});}
await b.close();})();
