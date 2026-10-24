# Lantern District

A personal VS Code setup for Windows, macOS and Linux: midnight navy, cyan light and warm amber. Code and command popups use 16px Cascadia Code; Explorer labels use 14px. Smooth block cursors and compact spacing are included.

## Install on Windows

1. Install Microsoft VS Code, Python 3.10 or newer, Git, and the [Cascadia Code font](https://github.com/microsoft/cascadia-code). Add VS Code's `code` command to PATH during installation. Fonts are not bundled here.
2. Clone this repository and open PowerShell in its folder.
3. Preview the changes, then install the theme and language extensions:

```powershell
git clone https://github.com/Doan-MHV/vscode-config.git
cd vscode-config
py setup.py install --extensions --dry-run
py setup.py install --extensions
```

On macOS/Linux, use `python3` instead of `py`. The installer selects the local VS Code settings path, backs up the original, merges only the shared preferences, and installs the local theme. It preserves unrelated preferences and JSONC comments. Run `python3 setup.py --help` for the supported commands. Language compilers and SDKs are installed separately; extensions provide editor integration.

The preset uses PATH and extension discovery rather than copying Mac compiler, Node, Python, .NET, JDK, vcpkg, SDK or adb paths. Existing local tool settings remain yours. Keep machine-specific overrides in your local User Settings; do not add them to this repository.

## Match the rounded Explorer and popup design

Colors, file icons and editor settings use VS Code's supported APIs. Matching UI fonts, rounded tab highlights and the Explorer styling need the optional local CSS patch:

```powershell
py setup.py apply-style
```

Use **Developer: Reload Window** afterward. This modifies only the local workbench stylesheet and creates an exact backup. VS Code can show its modified-installation warning, and updates can replace the patch. Integrity checks remain enabled. Re-run `apply-style` after an update if needed. `remove-style` restores the original workbench HTML when no unrelated changes have occurred. Default `install` does not patch the application.

If the installer cannot find your VS Code installation, use `apply-style --app-root` with its `resources/app` directory. A system-wide installation may require an elevated terminal. User installations normally avoid that. Use `--help` before overriding paths. This targets Microsoft VS Code Stable; forks, remote hosts and Insiders require separate configuration.

The original layout also uses **Customize Layout → Quick Input Position → Center**, with Outline and Timeline hidden through Explorer's menu. Sidebar width and these UI layout choices are not all represented by settings.json. Set them manually; do not copy VS Code's state database between computers.

## Language tools on Windows

| Language | Install separately | Local setup |
| --- | --- | --- |
| C/C++ | Visual Studio Build Tools with Desktop development with C++, CMake, Ninja, vcpkg | Select the compiler kit in CMake Tools. Use a Developer PowerShell when building with MSVC. Set `VCPKG_ROOT` to your local vcpkg checkout. |
| Python | Python and a project `.venv` | Run **Python: Select Interpreter**. Pylance supplies completions; Ruff formats and fixes imports on save. |
| C# | Official .NET SDK required by your project | C# / C# Dev Kit handle IntelliSense and debugging. Keep organizational C# Dev Kit licensing requirements in mind. |
| JS/TS | Node.js and each project's npm dependencies | Use the project's lockfile and TypeScript/ESLint/Prettier versions. VS Code includes JS/TS IntelliSense. |
| Kotlin/Android | Android Studio, Android SDK, project-compatible JDK, project Gradle Wrapper | Set the Windows SDK/JDK locations locally. Run `gradlew.bat` on Windows. Use Android Studio Device Manager for AVDs and Logcat Lens for its VS Code panel. |

Do not set `java.jdt.ls.java.home` to the Android build JDK. The platform-specific Java extension supplies its own language-server runtime; the universal extension currently needs Java 25+. The project's Gradle JDK is a separate choice and must match that project. This prevents the previous Java runtime mismatch.

For C++, `templates/CMakePresets.json` connects a project to `$env{VCPKG_ROOT}` without pinning `arm64-osx` or a Mac compiler. Add it to a CMake project that has its own `CMakeLists.txt` and `vcpkg.json`; select the correct compiler environment first. Keep `CMakeUserPresets.json` local. Microsoft C/C++ supplies the Windows MSVC debugger (`cppvsdbg`); CodeLLDB is an optional separate choice for Clang/LLDB projects.

Do not copy the old Mac starter project build folders or machine-specific launch settings to Windows. Android package IDs, module names, launch activities and emulator names belong to each project.

## Performance

The theme extension contains JSON/SVG only, and the UI patch is static CSS. `setup.py` runs only when invoked; there is no service, scheduled job or background customization process. Pylance diagnostics are limited to open files. Java's Kotlin support stays off so the JetBrains Kotlin server handles Kotlin. The requested native cursor animation remains enabled.

Open the project you are working on instead of the whole configuration directory. The template project ignore file excludes generated builds, caches, dependency folders and virtual environments from Git. For unusually large projects, configure watcher/search exclusions at project scope after checking which paths are generated. See [PERFORMANCE.md](PERFORMANCE.md) for the measured Mac snapshot and its limits.

## Sharing and restoring

Publish **the contents of this folder** as the repository root. Do not upload all of `~/.config`, the older `development` directory, `backups`, extension caches, login files, SDKs or VS Code's User directory. This export was assembled from an explicit list of appearance settings, language preferences and original theme assets; it is not a copy of the live profile.

`.local/`, local overrides, Python bytecode, generated VSIX/ZIP files and environment files are ignored. The installer saves its own backups in `.local/`. To restore the preferences from the latest successful install while preserving edits you made afterward:

```powershell
py setup.py restore
```

Restoring preferences does not uninstall language extensions. `remove-style` handles the optional CSS separately. No settings backup or account/session data is included in this repository. Sign in to Copilot or other account services separately on each computer.

The installer was exercised with temporary profiles on macOS and with Windows path-selection tests. Windows compilers, SDKs, emulator deployment and native UI rendering still need verification on a Windows machine.

## References

- [VS Code extension installation and CLI](https://code.visualstudio.com/docs/configure/extensions/extension-marketplace)
- [Microsoft vcpkg with CMake and VS Code](https://learn.microsoft.com/en-us/vcpkg/get_started/get-started-vscode)
- [Java extension runtime requirements](https://github.com/redhat-developer/vscode-java#requirements)
