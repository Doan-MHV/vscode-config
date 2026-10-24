"""Temporary-profile checks; never reads or changes the real VS Code profile."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location('lantern_setup', Path(__file__).parents[1] / 'setup.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class SettingsTests(unittest.TestCase):
    def test_strings_comments_and_trailing_commas_survive(self):
        text = '// header\n{\n  "url": "https://host/a//b/*c*/", // keep\n  "editor.fontSize": 18,\n  "list": [1, 2,],\n}\n'
        updated = setup.merge_settings(text, {'editor.fontSize': 16, 'editor.cursorStyle': 'block'})
        parsed = setup.parse_jsonc(updated)[0]
        self.assertEqual(parsed['url'], 'https://host/a//b/*c*/')
        self.assertEqual(parsed['list'], [1, 2])
        self.assertEqual(parsed['editor.fontSize'], 16)
        self.assertIn('// header', updated)
        self.assertIn('// keep', updated)

    def test_nested_preferences_and_comments_survive(self):
        text = '{"[python]": {\n  // user preference\n  "editor.tabSize": 8,\n  "editor.formatOnSave": false,\n}, "other": true}'
        updated = setup.merge_settings(text, {'[python]': {'editor.formatOnSave': True, 'editor.defaultFormatter': 'charliermarsh.ruff'}})
        parsed = setup.parse_jsonc(updated)[0]
        self.assertEqual(parsed['[python]']['editor.tabSize'], 8)
        self.assertTrue(parsed['[python]']['editor.formatOnSave'])
        self.assertIn('// user preference', updated)
        self.assertTrue(parsed['other'])

    def test_bom_crlf_and_unicode_preserved(self):
        text = '\ufeff{\r\n  // 日本語\r\n  "value": "a\\\"b",\r\n}\r\n'
        updated = setup.merge_settings(text, {'new': 3})
        self.assertTrue(updated.startswith('\ufeff'))
        self.assertIn('// 日本語\r\n', updated)
        self.assertEqual(setup.parse_jsonc(updated)[0], {'value': 'a"b', 'new': 3})

    def test_duplicate_keys_fail_before_writing(self):
        for text in ['{"a": 1, "a": 2}', '{"a": {"x": 1, "x": 2}}', '{/* missing end}']:
            with self.assertRaises(ValueError):
                setup.merge_settings(text, {'a': 3})

    def test_restore_keeps_later_edits_and_removes_added_keys(self):
        original = '{"size": 12, "unrelated": "keep"}'
        applied = setup.merge_settings(original, {'size': 16, 'new1': True, 'new2': False})
        changes = {'size': {'present': True, 'value': 12, 'applied': 16},
                   'new1': {'present': False, 'value': None, 'applied': True},
                   'new2': {'present': False, 'value': None, 'applied': False}}
        later = setup.merge_settings(applied, {'size': 19})
        result, restored = setup.restored_settings(later, changes)
        self.assertEqual(setup.parse_jsonc(result)[0], {'size': 19, 'unrelated': 'keep'})
        self.assertEqual(set(restored), {'new1', 'new2'})

    def test_restore_adjacent_first_last_and_all_keys(self):
        for text in ['{"a":1,"b":2,"c":3}', '{"a":1,"b":2,"c":3,}']:
            for keys in [('a',), ('b',), ('c',), ('a','b'), ('b','c'), ('a','b','c')]:
                before = setup.parse_jsonc(text)[0]
                changes = {k: {'present': False, 'value': None, 'applied': before[k]} for k in keys}
                result, _ = setup.restored_settings(text, changes)
                self.assertEqual(setup.parse_jsonc(result)[0], {k:v for k,v in before.items() if k not in keys})


class TemporaryProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.local = self.root / '.local'
        self.addCleanup(patch.stopall)
        patch.object(setup, 'ROOT', self.root).start()
        patch.object(setup, 'LOCAL', self.local).start()
        (self.root / 'settings.json').write_text(json.dumps({'editor.fontSize': 16, '[python]': {'editor.formatOnSave': True}}))
        (self.root / 'extensions.json').write_text(json.dumps({'recommendations': ['ms-python.python']}))
        theme = self.root / 'theme'
        theme.mkdir()
        (theme / 'package.json').write_text(json.dumps({'name':'test-theme', 'publisher':'test', 'version':'1.0.0', 'engines':{'vscode':'^1.100.0'}, 'contributes':{'themes':[]}}))
        (theme / 'LICENSE').write_text('MIT')
        (theme / 'README.md').write_text('Test data theme')
        styles = self.root / 'styles'
        styles.mkdir()
        (styles / 'popup-font.css').write_text('.popup {font-size:16px;}')
        (styles / 'workbench.css').write_text('.tab {border-radius:6px;}')
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def test_dry_run_does_not_create_backups_or_install(self):
        target = self.root / 'profile/settings.json'
        args = argparse.Namespace(settings=str(target), extensions=True, code=None, dry_run=True)
        with patch.object(setup.subprocess, 'run') as run:
            setup.install(args)
        run.assert_not_called()
        self.assertFalse(target.exists())
        self.assertFalse(self.local.exists())

    def test_install_backup_and_restore_roundtrip(self):
        target = self.root / 'settings.jsonc'
        original = b'// my config\n{"localOnly":true,"editor.fontSize":12,"[python]":{"editor.tabSize":8,}}\n'
        target.write_bytes(original)
        args = argparse.Namespace(settings=str(target), extensions=True, code=None, dry_run=False)
        with patch.object(setup, 'code_command', return_value=(['code'], {})), patch.object(setup.subprocess, 'run') as run:
            setup.install(args)
            self.assertEqual(run.call_count, 2)
        data = setup.parse_jsonc(target.read_text())[0]
        self.assertEqual(data['[python]']['editor.tabSize'], 8)
        self.assertTrue(data['localOnly'])
        pointer = json.loads((self.local / 'latest-settings.json').read_text())
        backup = self.local / pointer['backup']
        self.assertEqual((backup / 'settings.jsonc').read_bytes(), original)
        setup.restore(argparse.Namespace(settings=None, backup=None, dry_run=False))
        self.assertEqual(setup.parse_jsonc(target.read_text())[0], setup.parse_jsonc(original.decode())[0])
        self.assertIn('// my config', target.read_text())

    def test_packaged_theme_contains_only_data(self):
        vsix = setup.theme_package()
        with zipfile.ZipFile(vsix) as archive:
            self.assertEqual(archive.testzip(), None)
            self.assertIn('extension/package.json', archive.namelist())
            self.assertIn(b'ExecutesCode', archive.read('extension.vsixmanifest'))
        package = self.root / 'theme/package.json'
        data = json.loads(package.read_text())
        data['main'] = './malicious.js'
        package.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            setup.theme_package()

    def test_css_roundtrip_and_csp_preserved(self):
        app = self.root / 'app'
        app.mkdir()
        (app / 'package.json').write_text('{"name":"Code"}')
        (app / 'product.json').write_text('{"applicationName":"code","nameLong":"Visual Studio Code"}')
        target = app / 'out/vs/code/electron-browser/workbench/workbench.html'
        target.parent.mkdir(parents=True)
        original = b'<html>\r\n<head><meta http-equiv="Content-Security-Policy" content="script-src none"></head>\r\n<body></body></html>\r\n'
        target.write_bytes(original)
        args = argparse.Namespace(app_root=str(app), dry_run=False)
        setup.change_style(args)
        self.assertIn(b'script-src none', target.read_bytes())
        first = target.read_bytes()
        setup.change_style(args)
        self.assertEqual(target.read_bytes(), first)
        setup.change_style(args, remove=True)
        self.assertEqual(target.read_bytes(), original)

    def test_wrong_editor_or_unsafe_css_rejected(self):
        app = self.root / 'other'
        app.mkdir()
        (app / 'package.json').write_text('{"name":"OtherEditor"}')
        (app / 'product.json').write_text('{}')
        with self.assertRaises(ValueError):
            setup.app_root(str(app))
        with self.assertRaises(ValueError):
            setup.strip_style(setup.BEGIN + '<style>')


class PlatformTests(unittest.TestCase):
    def test_windows_settings_uses_appdata(self):
        with patch.object(setup.sys, 'platform', 'win32'), patch.dict(os.environ, {'APPDATA': '/fixture/Roaming'}):
            self.assertEqual(setup.settings_path(), Path('/fixture/Roaming/Code/User/settings.json'))

    def test_linux_settings_uses_xdg(self):
        with patch.object(setup.sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_CONFIG_HOME': '/fixture/config'}):
            self.assertEqual(setup.settings_path(), Path('/fixture/config/Code/User/settings.json'))

    def test_windows_launcher_uses_electron_without_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary) / 'Microsoft VS Code'
            (app / 'bin').mkdir(parents=True)
            (app / 'resources/app/out').mkdir(parents=True)
            for path in [app/'bin/code.cmd', app/'Code.exe', app/'resources/app/out/cli.js']:
                path.touch()
            with patch.object(setup.sys, 'platform', 'win32'):
                command, env = setup.code_command(str(app/'bin/code.cmd'))
            self.assertEqual(command, [str((app/'Code.exe').resolve()), str((app/'resources/app/out/cli.js').resolve())])
            self.assertEqual(env['ELECTRON_RUN_AS_NODE'], '1')


if __name__ == '__main__':
    unittest.main()
