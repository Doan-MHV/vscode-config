#!/usr/bin/env python3
"""Install a portable VS Code appearance and optional developer extensions.

Python 3 standard library only. This script runs on demand, never as a service.
Application CSS styling is an explicit, separate opt-in command.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / ".local"
BEGIN = "<!-- LANTERN_DISTRICT_POPUP_FONT_BEGIN -->"
END = "<!-- LANTERN_DISTRICT_POPUP_FONT_END -->"
AGY_BEGIN = "<!-- LANTERN_DISTRICT_ANTIGRAVITY_STYLE_BEGIN -->"
AGY_END = "<!-- LANTERN_DISTRICT_ANTIGRAVITY_STYLE_END -->"
STYLE_PATTERN = re.compile(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END) + r"\r?\n?")
AGY_STYLE_PATTERN = re.compile(re.escape(AGY_BEGIN) + r"[\s\S]*?" + re.escape(AGY_END) + r"\r?\n?")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def json_equal(left, right):
    # Python otherwise considers True and 1 equal, unlike JSON settings types.
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(right, sort_keys=True, ensure_ascii=False)


def atomic_write(path, data):
    """Replace one file atomically, retaining its access mode when it exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".lantern-", delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON property {key!r}; resolve it before applying settings.")
        result[key] = value
    return result


def mask_comments(text):
    """Mask JSONC comments without changing offsets or touching string contents."""
    result = list(text)
    i = 1 if text.startswith("\ufeff") else 0
    if i:
        result[0] = " "
    while i < len(text):
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            end = len(text) if end == -1 else end
            result[i:end] = " " * (end - i)
            i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                raise ValueError("Unterminated JSONC comment.")
            end += 2
            for position in range(i, end):
                if text[position] not in "\r\n":
                    result[position] = " "
            i = end
        else:
            i += 1
    return "".join(result)


def parse_jsonc(text):
    """Read JSONC and record exact top-level key/value offsets for small edits."""
    masked = mask_comments(text)
    clean = list(masked)
    i = 0
    decoder = json.JSONDecoder(object_pairs_hook=unique_object)
    while i < len(masked):
        if masked[i] == '"':
            _, i = decoder.raw_decode(masked, i)
        elif masked[i] == ",":
            following = i + 1
            while following < len(masked) and masked[following].isspace():
                following += 1
            if following < len(masked) and masked[following] in "]}":
                clean[i] = " "
            i += 1
        else:
            i += 1
    clean = "".join(clean)
    data = json.loads(clean, object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise ValueError("VS Code settings must contain a JSON object.")
    position = 0

    def skip_space(index):
        while index < len(clean) and clean[index].isspace():
            index += 1
        return index

    position = skip_space(position) + 1  # Opening object brace, checked by json.loads.
    properties = {}
    position = skip_space(position)
    while clean[position] != "}":
        key_start = position
        key, position = decoder.raw_decode(clean, position)
        position = skip_space(position) + 1  # Colon.
        value_start = skip_space(position)
        _, value_end = decoder.raw_decode(clean, value_start)
        properties[key] = (key_start, value_start, value_end)
        position = skip_space(value_end)
        if clean[position] == ",":
            position = skip_space(position + 1)
    return data, properties, position, masked


def apply_edits(text, edits):
    # A removal may encounter the same separator from two adjacent properties.
    for start, end, replacement in sorted(set(edits), reverse=True):
        text = text[:start] + replacement + text[end:]
    parse_jsonc(text)  # Never write malformed output.
    return text


def merge_settings(text, wanted):
    current, properties, closing, masked = parse_jsonc(text)
    edits = []
    missing = {}
    for key, value in wanted.items():
        if key in properties:
            if isinstance(current[key], dict) and isinstance(value, dict):
                _, start, end = properties[key]
                merged = merge_settings(text[start:end], value)
                if merged != text[start:end]:
                    edits.append((start, end, merged))
            elif not json_equal(current[key], value):
                _, start, end = properties[key]
                edits.append((start, end, json.dumps(value, ensure_ascii=False, indent=2)))
        else:
            missing[key] = value
    if missing:
        newline = "\r\n" if "\r\n" in text else "\n"
        indent = "  "
        line_start = text.rfind("\n", 0, closing) + 1
        closing_indent = text[line_start:closing]
        insert_at = line_start if closing_indent and closing_indent.isspace() else closing
        comma_prefix = ""
        if properties:
            first_start = next(iter(properties.values()))[0]
            prefix = text[text.rfind("\n", 0, first_start) + 1:first_start]
            if prefix and prefix.isspace():
                indent = prefix
            last_end = next(reversed(properties.values()))[2]
            if "," not in masked[last_end:closing]:
                if last_end == insert_at:
                    comma_prefix = ","
                else:
                    edits.append((last_end, last_end, ","))
        entries = []
        for key, value in missing.items():
            formatted = json.dumps(value, ensure_ascii=False, indent=2).replace("\n", newline + indent)
            entries.append(indent + json.dumps(key) + ": " + formatted)
        leading = "" if text[:insert_at].endswith("\n") else newline
        edits.append((insert_at, insert_at, comma_prefix + leading + ("," + newline).join(entries) + "," + newline))
    return apply_edits(text, edits)


def restored_settings(text, changes):
    current, properties, closing, masked = parse_jsonc(text)
    edits = []
    restored = []
    items = list(properties.items())
    for index, (key, (key_start, start, end)) in enumerate(items):
        before = changes.get(key)
        if before is None or not json_equal(current[key], before["applied"]):
            continue
        restored.append(key)
        if before["present"]:
            value_text = before.get("originalText", json.dumps(before["value"], ensure_ascii=False, indent=2))
            edits.append((start, end, value_text))
        else:
            edits.append((key_start, end, ""))
            next_start = items[index + 1][1][0] if index + 1 < len(items) else closing
            separator = masked.find(",", end, next_start)
            if separator == -1 and index:
                separator = masked.find(",", items[index - 1][1][2], key_start)
            if separator != -1:
                edits.append((separator, separator + 1, ""))
    return apply_edits(text, edits), restored


def settings_path(override=None):
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    for folder in ("Antigravity IDE", "Antigravity", "Code"):
        candidate = base / folder / "User/settings.json"
        if candidate.exists() or (base / folder).exists():
            return candidate
    return base / "Antigravity IDE/User/settings.json"


def backup_directory(label):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = LOCAL / "backups" / f"{stamp}-{label}-{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True, mode=0o700)
    return directory


def code_command(override=None):
    found = override
    if not found:
        for name in ("antigravity-ide", "antigravity-ide.cmd", "agy-ide", "agy-ide.cmd", "antigravity", "antigravity.cmd", "code", "code.cmd"):
            found = shutil.which(name)
            if found:
                break
    if not found:
        fallback_candidates = []
        if sys.platform == "win32":
            bases = [Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Programs", Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))]
            for base in bases:
                fallback_candidates.extend([
                    base / "Antigravity IDE/bin/antigravity-ide.cmd",
                    base / "Antigravity/bin/antigravity.cmd",
                    base / "Microsoft VS Code/bin/code.cmd",
                ])
        elif sys.platform == "darwin":
            for base in [Path("/Applications"), Path.home() / "Applications"]:
                fallback_candidates.extend([
                    base / "Antigravity IDE.app/Contents/Resources/app/bin/antigravity-ide",
                    base / "Antigravity.app/Contents/Resources/app/bin/antigravity",
                    base / "Visual Studio Code.app/Contents/Resources/app/bin/code",
                ])
        for path in fallback_candidates:
            if path.is_file():
                found = str(path)
                break
    if not found:
        raise ValueError("Antigravity IDE / VS Code CLI not found. Add 'antigravity-ide' (or 'code') to PATH or pass --code PATH.")
    candidate = Path(found).expanduser()
    if not candidate.is_file():
        found = shutil.which(str(found))
        if not found:
            raise ValueError("The --code command was not found.")
        candidate = Path(found)
    candidate = candidate.resolve()
    env = os.environ.copy()
    if sys.platform == "win32" and candidate.suffix.lower() in {".cmd", ".bat", ".exe"}:
        # Avoid cmd.exe and all shell interpolation. This is what the official
        # launcher does internally: run the vendor's CLI with its own Electron.
        install = candidate.parent.parent if candidate.suffix.lower() in {".cmd", ".bat"} else candidate.parent
        cli = install / "resources/app/out/cli.js"
        executable = None
        for exe_name in ("Antigravity IDE.exe", "Antigravity.exe", "Code.exe"):
            if (install / exe_name).is_file():
                executable = install / exe_name
                break
        if not executable or not cli.is_file():
            raise ValueError("Cannot locate Antigravity IDE.exe / Code.exe and CLI beside this Windows launcher. Pass the standard executable or bin/*.cmd path.")
        env["ELECTRON_RUN_AS_NODE"] = "1"
        return [str(executable), str(cli)], env
    return [str(candidate)], env


def theme_package(dry_run=False):
    source = ROOT / "theme"
    package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    if any(key in package for key in ("main", "browser", "activationEvents", "extensionDependencies", "extensionPack", "dependencies", "devDependencies", "scripts")):
        raise ValueError("The theme must remain data-only, with no executable entry point or dependencies.")
    if set(package.get("contributes", {})) - {"themes", "iconThemes"}:
        raise ValueError("Only color themes and icon themes are allowed in this package.")
    name, version, publisher = (package[key] for key in ("name", "version", "publisher"))
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", value) for value in (name, version, publisher)):
        raise ValueError("Invalid theme package identity.")
    files = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Theme assets must not contain symbolic links.")
        if path.is_file():
            if path.suffix.lower() not in {".json", ".svg", ".md"} and path.name != "LICENSE":
                raise ValueError(f"Unexpected theme asset: {path.name}")
            files.append(path)
    destination = LOCAL / f"{name}-{version}.vsix"
    if dry_run:
        print(f"Would build {destination.name} from {len(files)} data-only theme assets.")
        return destination
    manifest = ET.Element("PackageManifest", {"Version": "2.0.0", "xmlns": "http://schemas.microsoft.com/developer/vsx-schema/2011"})
    metadata = ET.SubElement(manifest, "Metadata")
    ET.SubElement(metadata, "Identity", {"Language": "en-US", "Id": name, "Version": version, "Publisher": publisher})
    ET.SubElement(metadata, "DisplayName").text = package.get("displayName", name)
    ET.SubElement(metadata, "Description", {"xml:space": "preserve"}).text = package.get("description", "Color and file icon themes")
    ET.SubElement(metadata, "Categories").text = "Themes"
    properties = ET.SubElement(metadata, "Properties")
    for key, value in {"Engine": package["engines"]["vscode"], "ExtensionDependencies": "", "ExtensionPack": "", "LocalizedLanguages": "", "ExecutesCode": "false"}.items():
        ET.SubElement(properties, "Property", {"Id": "Microsoft.VisualStudio.Code." + key, "Value": value})
    ET.SubElement(metadata, "License").text = "extension/LICENSE"
    ET.SubElement(ET.SubElement(manifest, "Installation"), "InstallationTarget", {"Id": "Microsoft.VisualStudio.Code"})
    ET.SubElement(manifest, "Dependencies")
    assets = ET.SubElement(manifest, "Assets")
    for kind, path in [("Microsoft.VisualStudio.Code.Manifest", "package.json"), ("Microsoft.VisualStudio.Services.Content.Details", "README.md"), ("Microsoft.VisualStudio.Services.Content.License", "LICENSE")]:
        ET.SubElement(assets, "Asset", {"Type": kind, "Path": "extension/" + path, "Addressable": "true"})
    types = ET.Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
    for extension, mime in [("json", "application/json"), ("svg", "image/svg+xml"), ("md", "text/markdown"), ("vsixmanifest", "text/xml"), ("", "text/plain")]:
        ET.SubElement(types, "Default", {"Extension": extension, "ContentType": mime})
    LOCAL.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=LOCAL, suffix=".vsix", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("extension.vsixmanifest", ET.tostring(manifest, encoding="utf-8", xml_declaration=True))
            archive.writestr("[Content_Types].xml", ET.tostring(types, encoding="utf-8", xml_declaration=True))
            for path in files:
                archive.write(path, "extension/" + path.relative_to(source).as_posix())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    print(f"Built {destination}")
    return destination


def install(args):
    target = settings_path(args.settings)
    original = target.read_bytes() if target.exists() else None
    text = original.decode("utf-8") if original else "{}\n"
    preset = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    current, properties, _, _ = parse_jsonc(text)
    updated = merge_settings(text, preset)
    applied, _, _, _ = parse_jsonc(updated)
    changed = {key: {"present": key in current, "value": current.get(key), "applied": applied[key]}
               for key in preset if key not in current or not json_equal(current[key], applied[key])}
    for key, change in changed.items():
        if key in properties:
            _, start, end = properties[key]
            change["originalText"] = text[start:end]
    extensions = []
    if args.extensions:
        extensions = json.loads((ROOT / "extensions.json").read_text(encoding="utf-8"))["recommendations"]
        if not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+", item) for item in extensions):
            raise ValueError("Invalid extension recommendation ID.")
    if args.dry_run:
        theme_package(dry_run=True)
        print(f"Would merge {len(changed)} preferences into {target} without changing unrelated settings/comments.")
        print(f"Would install the theme and {len(extensions)} optional developer extensions. App CSS stays unchanged.")
        return
    command, env = code_command(args.code)
    vsix = theme_package()
    subprocess.run(command + ["--install-extension", str(vsix), "--force"], env=env, check=True)
    for extension in extensions:
        subprocess.run(command + ["--install-extension", extension], env=env, check=True)
    if changed:
        backup = backup_directory("settings")
        (backup / "settings.jsonc").write_bytes(original or b"")
        (backup / "changes.json").write_text(json_text({"target": str(target), "settingsExisted": original is not None, "changes": changed}), encoding="utf-8")
        atomic_write(target, updated.encode("utf-8"))
        atomic_write(LOCAL / "latest-settings.json", json_text({"backup": str(backup.relative_to(LOCAL))}).encode("utf-8"))
        print(f"Merged {len(changed)} preferences. Exact backup: {backup}")
    else:
        print("All preset preferences already match; no settings file was rewritten.")
    print("Reload VS Code. Install your chosen code font separately. Optional CSS: python setup.py apply-style")


def restore(args):
    if args.backup:
        backup = Path(args.backup).expanduser().resolve()
    else:
        pointer = json.loads((LOCAL / "latest-settings.json").read_text(encoding="utf-8"))
        backup = LOCAL / pointer["backup"]
    record = json.loads((backup / "changes.json").read_text(encoding="utf-8"))
    target = settings_path(args.settings) if args.settings else Path(record["target"])
    original = target.read_bytes() if target.exists() else b"{}\n"
    updated, restored = restored_settings(original.decode("utf-8"), record["changes"])
    if args.dry_run:
        print(f"Would restore {len(restored)} preferences in {target}; later changed values are preserved.")
    elif restored:
        safety = backup_directory("before-restore")
        (safety / "settings.jsonc").write_bytes(original)
        atomic_write(target, updated.encode("utf-8"))
        print(f"Restored {len(restored)} preferences; later changes preserved. Safety backup: {safety}")
    else:
        print("No matching applied preferences remain to restore.")


def app_root(override=None):
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    else:
        for name in ("antigravity-ide", "antigravity-ide.cmd", "agy-ide", "agy-ide.cmd", "antigravity", "antigravity.cmd", "code", "code.cmd"):
            command = shutil.which(name)
            if command:
                launcher = Path(command).resolve()
                candidates.extend([launcher.parent.parent, launcher.parent.parent / "resources/app"])
        if sys.platform == "darwin":
            for base in [Path("/Applications"), Path.home() / "Applications"]:
                candidates.extend([
                    base / "Antigravity IDE.app/Contents/Resources/app",
                    base / "Antigravity.app/Contents/Resources/app",
                    base / "Visual Studio Code.app/Contents/Resources/app",
                ])
        elif sys.platform == "win32":
            bases = [Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Programs", Path(os.environ.get("PROGRAMFILES", "C:/Program Files")), Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))]
            for base in bases:
                candidates.extend([
                    base / "Antigravity IDE/resources/app",
                    base / "Antigravity/resources/app",
                    base / "Microsoft VS Code/resources/app",
                ])
        else:
            candidates.extend(Path(base) / "resources/app" for base in ["/usr/share/antigravity-ide", "/opt/antigravity-ide", "/usr/share/code", "/usr/lib/code", "/opt/visual-studio-code", "/snap/code/current/usr/share/code"])
    allowed_identities = {
        ("Antigravity IDE", "antigravity-ide", "Antigravity IDE"),
        ("Antigravity", "antigravity", "Antigravity"),
        ("Code", "code", "Visual Studio Code"),
    }
    for candidate in candidates:
        try:
            package = json.loads((candidate / "package.json").read_text(encoding="utf-8"))
            product = json.loads((candidate / "product.json").read_text(encoding="utf-8"))
            identity = (package.get("name"), product.get("applicationName"), product.get("nameLong"))
            if identity not in allowed_identities:
                continue
            target = candidate / "out/vs/code/electron-browser/workbench/workbench.html"
            if target.is_file():
                return candidate.resolve(), target.resolve()
        except (OSError, ValueError):
            continue
    raise ValueError("A verified Antigravity IDE (or VS Code) Resources/app folder was not found. Use --app-root PATH.")


def strip_style(html):
    for b, e in [(BEGIN, END), (AGY_BEGIN, AGY_END)]:
        if html.count(b) != html.count(e) or html.count(b) > 1:
            raise ValueError("Incomplete or duplicated style markers; app left unchanged.")
        if b in html and html.index(b) > html.index(e):
            raise ValueError("Invalid style marker order; app left unchanged.")
    return AGY_STYLE_PATTERN.sub("", STYLE_PATTERN.sub("", html))


def change_style(args, remove=False):
    _, target = app_root(args.app_root)
    original = target.read_bytes()
    html = original.decode("utf-8")
    plain = strip_style(html)
    baseline_pointer = LOCAL / "style-baseline.json"
    baseline = None
    if baseline_pointer.exists():
        record = json.loads(baseline_pointer.read_text(encoding="utf-8"))
        if record["target"] == str(target):
            candidate = LOCAL / record["file"]
            if candidate.is_file() and candidate.read_bytes() == plain.encode("utf-8"):
                baseline = candidate
    if remove:
        if BEGIN not in html:
            print("Optional workbench CSS is already absent.")
            return
        updated = baseline.read_bytes() if baseline else plain.encode("utf-8")
    else:
        css = "\n".join((ROOT / "styles" / name).read_text(encoding="utf-8") for name in ["popup-font.css", "workbench.css"])
        if any(token in css.lower() for token in ["</style", "<script", "@import", "url("]):
            raise ValueError("Only self-contained CSS is allowed; no scripts or external resources.")
        if plain.count("</head>") != 1:
            raise ValueError("Workbench HTML structure changed; app left unchanged.")
        block = BEGIN + '\n<style id="lantern-district-popup-font">\n' + css + "\n</style>\n" + END + "\n"
        updated = plain.replace("</head>", block + "</head>").encode("utf-8")
    if args.dry_run:
        print(f"Would {'remove' if remove else 'apply'} optional local CSS in {target}. No files changed.")
        return
    if updated == original:
        print("Optional workbench CSS already matches; no app file was rewritten.")
        return
    backup = backup_directory("style")
    (backup / "workbench.html").write_bytes(original)
    (backup / "target.json").write_text(json_text({"target": str(target)}), encoding="utf-8")
    if not remove and baseline is None:
        baseline = backup / "unmodified-workbench.html"
        baseline.write_bytes(plain.encode("utf-8"))
        atomic_write(baseline_pointer, json_text({"target": str(target), "file": str(baseline.relative_to(LOCAL))}).encode("utf-8"))
    atomic_write(target, updated)
    print(f"{'Removed' if remove else 'Applied'} optional workbench CSS. Backup: {backup}")
    print("Reload VS Code. Custom CSS triggers its modified-installation integrity warning; checks stay enabled. App updates may replace the CSS.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install_parser = commands.add_parser("install", help="Install the data-only theme and merge portable preferences.")
    install_parser.add_argument("--settings", help="Alternate VS Code User/settings.json path.")
    install_parser.add_argument("--code", help="Official VS Code CLI path, if code is not on PATH.")
    install_parser.add_argument("--extensions", action="store_true", help="Also install developer extension recommendations.")
    install_parser.add_argument("--dry-run", action="store_true", help="Validate and show planned changes without writing or installing.")
    restore_parser = commands.add_parser("restore", help="Restore preferences that still match the last applied values.")
    restore_parser.add_argument("--settings", help="Override the settings target recorded in the backup.")
    restore_parser.add_argument("--backup", help="Specific settings backup folder; default is latest install backup.")
    restore_parser.add_argument("--dry-run", action="store_true")
    build_parser = commands.add_parser("build-theme", help="Build a reusable local VSIX without installing it.")
    build_parser.add_argument("--dry-run", action="store_true")
    for name in ["apply-style", "remove-style"]:
        style_parser = commands.add_parser(name, help=("Apply" if name == "apply-style" else "Remove") + " optional app CSS, separately from supported theme settings.")
        style_parser.add_argument("--app-root", help="VS Code Stable Resources/app directory.")
        style_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "install":
        install(args)
    elif args.command == "restore":
        restore(args)
    elif args.command == "build-theme":
        theme_package(args.dry_run)
    else:
        change_style(args, remove=args.command == "remove-style")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
