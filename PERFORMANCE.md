# Performance Notes

- **Data-Only Theme & Icons**: The Lantern District `1.4.0` extension has no executable entry point, activation events, or runtime dependencies. Its color theme and 66 original SVG icons are static JSON/SVG assets.
- **Static CSS Patch**: The optional UI stylesheet (`styles/popup-font.css` and `styles/workbench.css`) is ~12 KB of self-contained CSS with no external resources, JavaScript, or continuous animations.
- **On-Demand Installer**: `setup.py` uses only the Python 3 standard library and runs only when invoked.
- **Lean Language Tooling**:
  - Python diagnostics (`python.pyrefly.diagnosticMode`) are scoped to `"openFilesOnly"`.
  - Heavy Java JDT, Gradle, and Android background language servers are excluded.
  - Error Lens is configured with a `500ms` delay, `error`/`warning` filter, and `"allLinesExceptActive"` cursor mode for zero typing jitter.
