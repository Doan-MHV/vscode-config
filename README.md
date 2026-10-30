# Lantern District — Antigravity IDE Config

A minimal, portable **Antigravity IDE** (and VS Code) setup for Windows, macOS, and Linux:
- **Lantern District `1.4.0` Theme & Icons**: Golden-hour twilight indigo (`#181726`, `#13121F`), sunset apricot (`#F2A365`), soft lavender (`#C4A7E7`), periwinkle (`#89B4FA`), coral (`#F28FAD`), and teal (`#8BD5CA`) syntax hierarchy, plus 66 centered `20×20` SVG file & folder icons.
- **Minimal UI**: Top activity bar, single-tab focus mode, clean 8px scrollbars without minimap, `16px` Cascadia Code across editor, command palette, and Explorer labels, smooth phase block cursor, and inline Error Lens diagnostics.
- **Languages Included**: C/C++ (`clangd` + CMake + LLDB), Python (`Pyrefly` + `Ruff` + `debugpy`), C# (`DotRush`), and JS/TS (`Prettier` + `ESLint`) (Java/Android/Gradle/Vim excluded).

## Install on Windows

1. Install **Antigravity IDE**, Python 3.10 or newer, Git, and the [Cascadia Code font](https://github.com/microsoft/cascadia-code).
2. Clone this repository and open PowerShell in its folder.
3. Preview the changes, then install the theme, settings, and extensions:

```powershell
git clone https://github.com/Doan-MHV/vscode-config.git
cd vscode-config
py setup.py install --extensions --dry-run
py setup.py install --extensions
py setup.py install-terminal
```

On macOS/Linux, use `python3` instead of `py`. The installer automatically locates your local **Antigravity IDE** User `settings.json` (`%APPDATA%\Antigravity IDE\User\settings.json` on Windows) and CLI (`antigravity-ide` / `agy-ide`), backs up your existing settings, merges only the shared preferences, and builds/installs the local `lantern-district` VSIX theme. Run `py setup.py --help` for all options.

## Terminal & Starship Setup (`terminal/`)

The `terminal/` directory bundles the matching **Lantern District** terminal and prompt configs:
- `terminal/starship.toml` — Starship prompt palette and Nerd Font language/git icons matching Antigravity IDE's Explorer icon colors (`py setup.py install-terminal` installs it to `~/.config/starship.toml`).
- `terminal/ghostty/config` & `terminal/ghostty/themes/Lantern District` — Ghostty terminal configuration and custom theme (`py setup.py install-terminal` installs both to `~/.config/ghostty/`).
- `terminal/windows-terminal-scheme.json` — Ready-to-use `Lantern District` color scheme for **Windows Terminal** (`settings.json` → `"schemes"`).
- `terminal/zsh/colors.zsh` — Zsh syntax highlighting and `EZA_COLORS` (`eza --icons=auto`) matching Lantern District file and folder icon colors.

## Apply the Explorer & Popup Styling (Optional CSS Patch)

To get the `16px` Explorer font, `20px` icon containers, and twilight indigo workbench polish:

```powershell
py setup.py apply-style
```

Then run **Developer: Reload Window** (`Ctrl+Shift+P` / `Cmd+Shift+P`). This modifies only the local `workbench.html` stylesheet and creates an exact backup in `.local/`. If an Antigravity IDE update overwrites `workbench.html`, simply re-run `py setup.py apply-style`. To revert at any time:

```powershell
py setup.py remove-style
```

## Language Tools on Windows

| Language | Install Separately | Local Setup |
| --- | --- | --- |
| **C/C++** | LLVM (`clangd`, `clang-format`), Visual Studio Build Tools / Clang, CMake, Ninja, vcpkg | Ensure `clangd` and `cmake` are on `PATH`. Set `VCPKG_ROOT` to your local vcpkg checkout. |
| **Python** | Python 3.10+ and project `.venv` | Run **Python: Select Interpreter**. Pyrefly supplies fast diagnostics; Ruff formats and organizes imports on save. |
| **C#** | Official .NET SDK | DotRush provides lightweight Roslyn completion, navigation, formatting, and debugging. |
| **JS/TS** | Node.js and project npm dependencies | Prettier formats on save and ESLint fixes code actions on save. |

For C++, `templates/CMakePresets.json` connects a project to `$env{VCPKG_ROOT}` without pinning Mac paths.

## Restoring Previous Settings

The installer saves backups in `.local/` (excluded from Git). To revert the merged settings while keeping any edits you made afterward:

```powershell
py setup.py restore
```
