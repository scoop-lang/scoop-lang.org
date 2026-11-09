"""Run the PowerShell installer against a local release server and an isolated user profile."""

import functools
import http.server
import os
import shutil
import subprocess
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[2] / "install.ps1"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

if os.name == "nt":
    import winreg


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        self.server.requests.append(self.path)


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "install.ps1 runs on Windows PowerShell")
class PowerShellInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scoop installer ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.profile = self.root / "user profile"
        self.profile.mkdir()
        self.releases = self.root / "releases"
        self.releases.mkdir()
        shutil.copyfile(INSTALLER, self.releases / "install.ps1")

        # Any console program that accepts --version and exits 0 stands in for sco.exe.
        tar = Path(os.environ["SystemRoot"]) / "System32" / "tar.exe"
        packages = {
            "bin": {
                "VERSION": "1.2.3\n",
                "bin/sco.exe": tar.read_bytes(),
                "commands/scoop-example.exe": b"example command",
                "post-install.ps1": b"""
Add-Content -LiteralPath "$env:USERPROFILE/post-install-arguments" -Value ($args -join ' ')
if ($env:TEST_POST_INSTALL_FAIL) { exit 23 }
New-Item -ItemType Directory -Force "$PSScriptRoot/lib/test-target", "$PSScriptRoot/docs" | Out-Null
Set-Content -LiteralPath "$PSScriptRoot/lib/test-target/scoop.core.slib" -Value 'compiled library'
Set-Content -LiteralPath "$PSScriptRoot/docs/index.html" -Value 'API documentation'
""",
            },
            "sources": {"src/scoop.core/Cone.toml": b'[cone]\nname = "scoop.core"\n'},
        }
        self.index_lines = ["format 1", "release 2026-11-07", "version 1.2.3"]
        self.index_lines.append("package linux 2026-11-07/linux/scoop-1.2.3-sources.tar.xz")
        for kind, files in packages.items():
            suffix = "sources" if kind == "sources" else "bin-x86_64-pc-windows-gnullvm"
            key = f"2026-11-07/windows/scoop-1.2.3-{suffix}.tar.xz"
            self.index_lines.append(f"package windows {key}")
            package = self.root / "package" / kind
            for relative, content in files.items():
                path = package / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            archive = self.releases / key
            archive.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(archive, "w:xz") as tar_file:
                tar_file.add(package, arcname=".")
        self.write_index()

        handler = functools.partial(QuietHandler, directory=str(self.releases))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.requests = []
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

        self.environment = dict(os.environ)
        self.environment.update(
            USERPROFILE=str(self.profile),
            TEMP=str(self.root),
            TMP=str(self.root),
            SCOOP_RELEASE_URL=self.base_url + "/",
        )
        self.environment.pop("TEST_POST_INSTALL_FAIL", None)

    def write_index(self, lines=None):
        content = "\n".join(self.index_lines if lines is None else lines) + "\n"
        for name in ("latest.txt", "2026-11-07/index.txt"):
            path = self.releases / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def run_powershell(self, *arguments, success=True):
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", *arguments],
            text=True,
            capture_output=True,
            env=self.environment,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def install(self, *arguments, success=True):
        return self.run_powershell(
            "-File", str(INSTALLER), "-NoModifyPath", *arguments, success=success
        )

    def user_path(self):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            try:
                return winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return None

    def test_install_and_upgrade_keep_user_data(self):
        install = self.profile / ".scoop"
        for relative in ("packages/cache", "commands/scoop-custom", "lib/old-target/old.slib"):
            path = install / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("existing data")
        before = self.user_path()
        for _ in range(2):
            result = self.install("--", "--jobs", "2")
        self.assertIn("Scoop is installed", result.stdout)
        self.assertEqual((install / "VERSION").read_text(), "1.2.3\n")
        self.assertTrue((install / "bin/sco.exe").is_file())
        self.assertTrue((install / "docs/index.html").is_file())
        self.assertTrue((install / "lib/test-target/scoop.core.slib").is_file())
        self.assertFalse((install / "lib/old-target").exists())
        for relative in ("packages/cache", "commands/scoop-custom"):
            self.assertEqual((install / relative).read_text(), "existing data")
        self.assertTrue((install / "commands/scoop-example.exe").is_file())
        arguments = (self.profile / "post-install-arguments").read_text().splitlines()
        self.assertEqual(arguments, ["--jobs 2", "--jobs 2"])
        self.assertEqual(self.user_path(), before)
        self.assertEqual(
            self.server.requests[:3],
            [
                "/latest.txt",
                "/2026-11-07/windows/scoop-1.2.3-bin-x86_64-pc-windows-gnullvm.tar.xz",
                "/2026-11-07/windows/scoop-1.2.3-sources.tar.xz",
            ],
        )
        self.assertEqual(list(self.root.glob("scoop-install.*")), [])

    def test_release_option_and_version_alias(self):
        self.install("-Release", "2026-11-07")
        self.install("-Version", "2026-11-07")
        self.assertEqual(self.server.requests[0], "/2026-11-07/index.txt")
        self.assertEqual(self.server.requests.count("/2026-11-07/index.txt"), 2)

    def test_piped_install_keeps_the_session_open_and_sets_path(self):
        before = self.user_path()
        self.addCleanup(self.restore_user_path, before)
        bin_directory = str(self.profile / ".scoop" / "bin")
        command = (
            f"irm {self.base_url}/install.ps1 | iex; irm {self.base_url}/install.ps1 | iex; "
            "Write-Output \"after:$(Get-Command sco.exe | ForEach-Object Source)\""
        )
        result = self.run_powershell("-Command", command)
        after = self.user_path()
        self.assertIn("after:" + str(Path(bin_directory) / "sco.exe"), result.stdout)
        entries = [entry.rstrip("\\").lower() for entry in after[0].split(";")]
        self.assertEqual(entries.count(bin_directory.lower()), 1)
        self.assertEqual(after[1], winreg.REG_EXPAND_SZ)

    def restore_user_path(self, value):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
            if value is None:
                winreg.DeleteValue(key, "Path")
            else:
                winreg.SetValueEx(key, "Path", 0, value[1], value[0])

    def test_post_install_failure_reports_its_exit_code(self):
        self.environment["TEST_POST_INSTALL_FAIL"] = "1"
        result = self.install(success=False)
        self.assertEqual(result.returncode, 23)
        self.assertNotIn("Scoop is installed", result.stdout)
        self.assertIn("rerun", result.stderr)

    def test_invalid_input_fails_before_installing(self):
        result = self.install("-Release", "../invalid", success=False)
        self.assertIn("invalid release name", result.stderr)
        self.assertEqual(self.server.requests, [])
        result = self.install("-Release", "2000-01-01", success=False)
        self.assertIn("could not download the release index", result.stderr)
        self.write_index([line for line in self.index_lines if " windows " not in line])
        result = self.install(success=False)
        self.assertIn("packages for windows are not ready yet", result.stderr)
        for entry in ("package windows ../outside.tar.xz", "package windows /etc/passwd"):
            self.write_index(self.index_lines + [entry])
            self.assertIn("invalid package", self.install(success=False).stderr)
        self.write_index(["format 2"] + self.index_lines[1:])
        self.assertIn("unsupported release index format", self.install(success=False).stderr)
        self.assertFalse((self.profile / ".scoop").exists())


if __name__ == "__main__":
    unittest.main()
