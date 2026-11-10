// shot_card.js HTML OUT.png [width] [height] : screenshot a card's HTML at its size (the Python playwright is gone after a restart)
const { chromium } = require('playwright');
(async () => {
  const [html, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: +(w || 1080), height: +(h || 1350) } });
  await pg.goto('file://' + html); await pg.evaluate('document.fonts.ready'); await pg.waitForTimeout(300);
  await pg.screenshot({ path: out }); await b.close(); console.log('ok', out);
})();
