// Loads the RiyaazCore block straight out of index.html (falls back to src/core.js),
// so the tests always exercise the code that ships.
const fs = require('fs'), path = require('path'), vm = require('vm');
function loadCore() {
  const root = path.join(__dirname, '..');
  let src;
  const html = path.join(root, 'index.html');
  if (fs.existsSync(html)) {
    const s = fs.readFileSync(html, 'utf8');
    const a = s.indexOf('// === RIYAAZ CORE START ==='), b = s.indexOf('// === RIYAAZ CORE END ===');
    if (a < 0 || b < 0) throw new Error('core markers not found in index.html');
    src = s.slice(a, b);
  } else src = fs.readFileSync(path.join(root, 'src', 'core.js'), 'utf8');
  const ctx = { Math, Float32Array, Float64Array, Uint32Array, Error };
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  return ctx.RiyaazCore;
}
module.exports = { loadCore };
