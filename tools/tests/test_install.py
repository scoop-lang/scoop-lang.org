"""Check the shell bootstrap with real curl, isolated homes and a native CLI boundary."""

import os
import subprocess
import unittest

from support import ROOT, server, temporary


@unittest.skipIf(os.name == "nt", "POSIX shell bootstrap")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary(self)
        self.user = self.root / "user with spaces"
        self.user.mkdir()
        self.site = self.root / "site"
        self.site.mkdir()
        manager = self.site / "manager"
        manager.write_text("""#!/bin/sh
set -eu
mkdir -p "$SCOOP_HOME"
printf '%s\\n' "$@" > "$SCOOP_HOME/arguments"
[ "${TEST_INSTALL_FAIL:-0}" = 0 ] || exit 23
mkdir -p "$SCOOP_HOME/bin"
cp "$0" "$SCOOP_HOME/bin/scoop-install"
cp "$0" "$SCOOP_HOME/bin/scoop"
""")
        self.url, self.requests = server(self, self.site)
        self.env = {
            **os.environ,
            "HOME": str(self.user),
            "SHELL": "/bin/bash",
            "SCOOP_INSTALL_URL": self.url + "/manager",
            "TMPDIR": str(self.root),
        }
        for name in (
            "SCOOP_HOME",
            "SCOOP_NO_MODIFY_PATH",
            "TEST_INSTALL_FAIL",
            "ZDOTDIR",
            "XDG_CONFIG_HOME",
        ):
            self.env.pop(name, None)

    def install(self, *args, success=True):
        result = subprocess.run(
            ["sh", str(ROOT / "install.sh"), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if success else 23, result.stdout + result.stderr
        )
        return result

    def test_default_bootstrap_and_idempotent_path(self):
        self.install()
        self.install()
        home = self.user / ".scoop"
        self.assertEqual(
            (home / "arguments").read_text().splitlines(), ["toolchain", "install"]
        )
        self.assertEqual(self.requests, [("GET", "/manager")] * 2)
        for name in (".bashrc", ".profile"):
            self.assertEqual(
                (self.user / name).read_text().count("# Scoop programming language"), 1
            )
        self.assertEqual(list((home / "tmp").iterdir()), [])

    def test_arguments_and_custom_home_path_quoting(self):
        home = self.root / "it's a 中文 home"
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
        self.install(*args)
        self.assertEqual(
            (home / "arguments").read_text().splitlines(),
            ["toolchain", "install", *args],
        )
        result = subprocess.run(
            ["sh", "-c", '. "$HOME/.profile"; . "$HOME/.profile"; command -v scoop'],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(home / "bin/scoop"))
        self.assertFalse((self.user / ".scoop").exists())

    def test_shell_locations_and_skip_path(self):
        self.env.update(SHELL="/bin/zsh", ZDOTDIR=str(self.root / "zsh"))
        self.install()
        self.assertTrue((self.root / "zsh/.zshrc").is_file())
        self.env.update(SHELL="/bin/fish", XDG_CONFIG_HOME=str(self.root / "config"))
        self.install()
        self.assertIn(
            "fish_add_path", (self.root / "config/fish/config.fish").read_text()
        )
        self.env.update(SHELL="/bin/sh", SCOOP_NO_MODIFY_PATH="1")
        self.install()
        self.assertFalse((self.user / ".profile").exists())

    def test_failure_preserves_exit_status_without_path_update(self):
        self.env["TEST_INSTALL_FAIL"] = "1"
        result = self.install("--target", "target-one", success=False)
        self.assertNotIn("Scoop is installed", result.stdout)
        self.assertFalse((self.user / ".bashrc").exists())
        self.assertEqual(list((self.user / ".scoop/tmp").iterdir()), [])

    def test_host_detection_and_help(self):
        mock = self.root / "commands"
        mock.mkdir()
        uname = mock / "uname"
        uname.write_text(
            '#!/bin/sh\ncase "$1" in -s) echo Darwin;; -m) echo x86_64;; esac\n'
        )
        uname.chmod(0o755)
        sysctl = mock / "sysctl"
        sysctl.write_text("#!/bin/sh\necho 1\n")
        sysctl.chmod(0o755)
        self.env["PATH"] = str(mock) + os.pathsep + self.env["PATH"]
        self.assertIn("aarch64-apple-darwin", self.install().stdout)
        self.requests.clear()
        self.assertIn("--target", self.install("--help").stdout)
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
