// Load the wrapped JSON directly from the repository to avoid runtime fetch issues.
// Path: frontend/src/utils -> go up three levels to project root, then into Backend/exports
// Fetch wrapped JSON. Behavior:
// - Requires an explicit selection stored on `window.__SELECTED_WRAPPED__` (set by BackupSelect).
// - If Tauri FS is available and the path is a filesystem path, use Tauri FS to read it.
// - If the path is a blob: or http(s): URL, use `fetch` to load it.
// - If nothing is selected, return null (do not fall back to any bundled public file).
const fetchData = async () => {
  let path = null;
  try {
    path = (typeof window !== 'undefined' && window.__SELECTED_WRAPPED__) ? window.__SELECTED_WRAPPED__ : null;
  } catch (e) {
    path = null;
  }

  if (!path) {
    console.warn('No wrapped JSON selected (window.__SELECTED_WRAPPED__ not set).');
    return null;
  }

  // If running in Tauri and the path looks like a filesystem path, try reading from disk.
  try {
    if (window && window.__TAURI__ && window.__TAURI__.fs && typeof window.__TAURI__.fs.readTextFile === 'function') {
      let p = path;
      if (p.startsWith('file://')) p = p.replace(/^file:\/\//, '');
      // Heuristic: absolute paths typically contain a /. If p contains :\ or / it's likely a filesystem path
      if (p.indexOf('/') >= 0 || p.indexOf('\\') >= 0) {
        try {
          const text = await window.__TAURI__.fs.readTextFile(p);
          return JSON.parse(text);
        } catch (e) {
          console.warn('Tauri fs.readTextFile failed for', p, e);
        }
      }
    }
  } catch (e) {
    console.warn('Tauri FS check failed', e);
  }

  // If path is a blob or an http(s) URL, use fetch
  try {
    if (path.startsWith('blob:') || path.startsWith('http://') || path.startsWith('https://')) {
      const r = await fetch(path);
      if (!r.ok) throw new Error('HTTP error ' + r.status);
      return await r.json();
    }
  } catch (e) {
    console.warn('Fetch failed for', path, e);
  }

  // As a last attempt, try a relative/local fetch (this may fail in many environments)
  try {
    const r = await fetch(path);
    if (!r.ok) throw new Error('HTTP error ' + r.status);
    return await r.json();
  } catch (e) {
    console.error('Unable to load wrapped JSON from selected path:', path, e);
    return null;
  }
};

export default fetchData;