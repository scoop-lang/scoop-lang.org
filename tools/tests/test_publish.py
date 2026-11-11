"""Verify explicit component mapping and immutable publication with a local R2 boundary."""

import importlib.util
import os
import subprocess
import sys
import unittest

import tomllib
from support import ROOT, server, temporary

spec = importlib.util.spec_from_file_location(
    "publish", ROOT / "tools/publish_release_index.py"
)
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary(self)
        self.document = {
            "schema": 1,
            "release": "1.2.3",
            "version": "1.2.3",
            "revision": "revision-one",
            "sources": "sources",
            "vendor": "vendor",
            "hosts": {},
            "targets": {},
            "archives": {},
        }
        # Filenames intentionally do not encode the host or component relationships.
        components = ["sources", "vendor"]
        for index, host in enumerate(publish.PLATFORMS):
            target, binary, base = f"target-{index}", f"bin-{index}", f"base-{index}"
            self.document["hosts"][host] = {
                "default-target": target,
                "targets": [target],
                "bin": binary,
            }
            self.document["targets"][target] = {"base": base}
            components.extend((binary, base))
        for index, component in enumerate(components):
            self.document["archives"][component] = {
                "path": f"archive-{index}.tar.xz",
                "size": 10,
                "sha256": "a" * 64,
            }
        self.source = self.root / "manifest.toml"
        self.source.write_text(publish.toml_text(self.document))
        self.output = self.root / "output"

    def run_publisher(self, *args, env=None):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/publish_release_index.py"),
                str(self.source),
                "--release-dir",
                "2026-11-11",
                "--output-dir",
                str(self.output),
                *args,
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_dry_run_maps_relationships_without_credentials(self):
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("SCOOP_RELEASE_R2_")
        }
        result = self.run_publisher("--dry-run", "--latest", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = tomllib.loads((self.output / "versions/1.2.3.toml").read_text())
        for component, platform in (
            ("sources", "macos"),
            ("vendor", "macos"),
            ("bin-1", "linux"),
            ("base-2", "windows"),
        ):
            self.assertIn(
                f"/2026-11-11/{platform}/", manifest["archives"][component]["path"]
            )
        self.assertEqual(
            tomllib.loads((self.output / "latest.toml").read_text())["manifest"],
            "versions/1.2.3.toml",
        )
        del self.document["archives"]["sources"]
        with self.assertRaises(ValueError):
            publish.rewrite(self.document, "2026-11-11", "https://example.org")

    def test_fixed_manifest_is_immutable_and_latest_is_explicit(self):
        remote = self.root / "r2"
        remote.mkdir()
        url, requests = server(self, remote, writable=True)
        env = {
            **os.environ,
            "SCOOP_RELEASE_R2_ENDPOINT": url,
            "SCOOP_RELEASE_R2_KEY_ID": "test-key",
            "SCOOP_RELEASE_R2_SECRET": "test-secret",
        }
        result = self.run_publisher(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((remote / "scoop-releases/latest.toml").exists())
        result = self.run_publisher("--latest", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Reused versions/1.2.3.toml", result.stdout)
        previous = (remote / "scoop-releases/latest.toml").read_bytes()
        self.document["revision"] = "different-build"
        self.source.write_text(publish.toml_text(self.document))
        result = self.run_publisher("--latest", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("another build", result.stderr)
        self.assertEqual((remote / "scoop-releases/latest.toml").read_bytes(), previous)
        self.assertFalse(any("list-type" in path for _, path in requests))


if __name__ == "__main__":
    unittest.main()
