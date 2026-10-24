# Performance check

Checked on the configured Mac on October 24, 2026, with the Homework4 Kotlin/Android project open. This is a local process/configuration audit, not a startup benchmark or a Windows performance measurement.

The Lantern District extension has no executable entry point, activation events or runtime dependencies. Its theme and 66 original SVG icons are data assets. The combined custom CSS is about 12KB, with no external resources, JavaScript, animation loop or blur filter. The Python setup scripts are idle files until run. No custom theme/background Python process was observed.

Two process snapshots showed about 1.0GiB of RSS for VS Code and its child processes, plus roughly 675MiB for the JetBrains Kotlin server. RSS is a point-in-time working set and can include shared pages; it is not an incremental memory cost or a promise of idle usage. CPU changed between snapshots; no sustained runaway process was established. The `code --status` memory values were inconsistent with process RSS, so they were not used.

Language tooling is the main cost in this workspace. Java JDT, Gradle integration and Kotlin are distinct services. Java's Kotlin support is disabled, and no duplicate C++ language engine is configured. Another Kotlin server on the machine belonged to Neovim. Those existing development processes were left intact.

No performance-driven removal of the theme or block-cursor animation was warranted. Closing unused projects and using per-project environments/dependencies are more useful than deleting inert configuration scripts. Keep generated builds, dependency folders and caches out of Git. Check **Developer: Open Process Explorer** and **Developer: Show Running Extensions** if a particular workspace becomes slow.
