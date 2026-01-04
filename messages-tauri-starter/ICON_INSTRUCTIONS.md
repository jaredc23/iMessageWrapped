Icon replacement instructions
===========================

1) Place your source image (preferably a square PNG, >=1024px) somewhere on disk. Example: `~/Desktop/icon-source.png`

2) From the project root (`messages-tauri-starter`), run the helper script:

```bash
./scripts/generate-icons.sh /path/to/icon-source.png
```

This will try to use ImageMagick (`magick` or `convert`) if available. On macOS it will also use `sips` and `iconutil` to generate an `.icns` file for the native bundle.

Files created or updated:
- `public/logo192.png`
- `public/logo512.png`
- `public/favicon.ico` (if ImageMagick is available)
- `src-tauri/icons/icon.png`
- `src-tauri/icons/icon.icns` (if `iconutil` is available)
- `src-tauri/icons/icon.ico` (not guaranteed; `magick` required)

3) After icons are generated, verify `public/manifest.json` and `src-tauri/tauri.conf.json` point to the expected files. This repo already references `favicon.ico`, `logo192.png`, and `logo512.png` in the web manifest and includes a `bundle.icon` array in `tauri.conf.json`.

4) To verify web app changes locally:

```bash
npm start
```

5) To rebuild the native app with Tauri (macOS):

```bash
npm run tauri:build
```

Notes:
- If `magick` (ImageMagick) is not installed, install it with `brew install imagemagick` for best results (ICO generation and better scaling). The script will still create PNGs using `sips`.
- If you'd like, I can run the script for you using the image you attached—confirm and I'll create the icons in `public/` and `src-tauri/icons/`.
