"""Run the PowerShell bootstrap through a local HTTP server and a console executable."""

import base64
import os
import shutil
import subprocess
import unittest

from support import ROOT, server, temporary

POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
if os.name == "nt":
    import winreg


def quoted(text):
    return "'" + str(text).replace("'", "''") + "'"


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "Windows PowerShell bootstrap")
class PowerShellInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build a small native entry point; component installation is tested in scoop-install.
        cls.fixture = ROOT / "tmp/bootstrap-manager.exe"
        cls.fixture.parent.mkdir(exist_ok=True)
        cls.fixture.unlink(missing_ok=True)
        source = ROOT / "tools/tests/fixtures/bootstrap-manager.cs"
        command = f"Add-Type -Path {quoted(source)} -OutputAssembly {quoted(cls.fixture)} -OutputType ConsoleApplication"
        subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.fixture.unlink(missing_ok=True)

    def setUp(self):
        self.root = temporary(self)
        self.user = self.root / "user profile"
        self.user.mkdir()
        self.site = self.root / "site"
        self.site.mkdir()
        shutil.copyfile(self.fixture, self.site / "manager.exe")
        shutil.copyfile(ROOT / "install.ps1", self.site / "install.ps1")
        self.url, self.requests = server(self, self.site)
        self.env = {
            **os.environ,
            "USERPROFILE": str(self.user),
            "TEMP": str(self.root),
            "TMP": str(self.root),
            "SCOOP_INSTALL_URL": self.url + "/manager.exe",
            "SCOOP_NO_MODIFY_PATH": "1",
        }
        self.env.pop("SCOOP_HOME", None)
        self.env.pop("TEST_INSTALL_FAIL", None)

    def run_ps(self, command):
        encoded = base64.b64encode(command.encode("utf-16-le")).decode()
        return subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded,
            ],
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def install(self, *args):
        return self.run_ps(
            "& ([scriptblock]::Create((irm "
            + self.url
            + "/install.ps1))) "
            + " ".join(map(quoted, args))
            + "; exit $LASTEXITCODE"
        )

    def test_forwarding_custom_home_and_cleanup(self):
        home = self.root / "it's a custom home"
        args = [
            "1.2.3",
            "--home",
            str(home),
            "--target",
            "target-one,target-two",
            "--component",
            "gui,profiling,vendor",
            "--skip-docs",
        ]
        before = self.user_path()
        result = self.install(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (home / "arguments").read_text(encoding="utf-8-sig").splitlines(),
            ["toolchain", "install", *args],
        )
        self.assertEqual(
            self.requests, [("GET", "/install.ps1"), ("GET", "/manager.exe")]
        )
        self.assertEqual(list((home / "tmp").iterdir()), [])
        self.assertEqual(self.user_path(), before)

    def test_pipe_and_user_path_deduplication(self):
        before = self.user_path()
        self.addCleanup(self.restore_path, before)
        self.env.pop("SCOOP_NO_MODIFY_PATH")
        result = self.run_ps(
            f"irm {self.url}/install.ps1 | iex; irm {self.url}/install.ps1 | iex; Write-Output ('after:' + (Get-Command sco.exe).Source); exit $LASTEXITCODE"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        bin_path = str(self.user / ".scoop/bin")
        self.assertIn("after:" + str(self.user / ".scoop/bin/sco.exe"), result.stdout)
        self.assertEqual(
            self.user_path()[0].lower().split(";").count(bin_path.lower()), 1
        )

    def test_native_failure_keeps_interactive_session_open(self):
        self.env["TEST_INSTALL_FAIL"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        result = self.run_ps(
            f"irm {self.url}/install.ps1 | iex; Write-Output 'still-open'; exit $LASTEXITCODE"
        )
        self.assertEqual(result.returncode, 23)
        self.assertIn("still-open", result.stdout)
        self.assertNotIn("Scoop is installed", result.stdout)
        self.assertEqual(list((self.user / ".scoop/tmp").iterdir()), [])

    @staticmethod
    def user_path():
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            try:
                return winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return None

    @staticmethod
    def restore_path(value):
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
        ) as key:
            if value is None:
                winreg.DeleteValue(key, "Path")
            else:
                winreg.SetValueEx(key, "Path", 0, value[1], value[0])


if __name__ == "__main__":
    unittest.main()
