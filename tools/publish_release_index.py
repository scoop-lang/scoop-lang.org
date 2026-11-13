#!/usr/bin/env python3
"""Publish a generated Scoop component manifest and, explicitly, its latest pointer."""

import argparse
import copy
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

import tomllib

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    "aarch64-apple-darwin": "macos",
    "x86_64-unknown-linux-gnu": "linux",
    "x86_64-pc-windows-gnullvm": "windows",
}


def toml_text(document):
    lines = []

    def table(values, prefix=()):
        if prefix:
            lines.extend(("", "[" + ".".join(json.dumps(key) for key in prefix) + "]"))
        for key, value in values.items():
            if not isinstance(value, dict):
                lines.append(
                    f"{json.dumps(key)} = {json.dumps(value, ensure_ascii=False)}"
                )
        for key, value in values.items():
            if isinstance(value, dict):
                table(value, (*prefix, key))

    table(document)
    return "\n".join(lines) + "\n"


def name(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._+-]*", value
    ):
        raise ValueError(f"Invalid release name: {value!r}")
    return value


def rewrite(document, release_dir, base_url):
    document = copy.deepcopy(document)
    if document["schema"] != 1:
        raise ValueError("Unsupported component manifest schema")
    name(document["version"])
    name(document["release"])
    name(release_dir)
    locations = {document["sources"]: "macos", document["vendor"]: "macos"}

    def assign(component, platform):
        previous = locations.setdefault(component, platform)
        if previous != platform:
            raise ValueError(f"Conflicting storage locations for {component}")

    for host, selection in document["hosts"].items():
        platform = PLATFORMS[host]
        if selection["default-target"] not in selection["targets"]:
            raise ValueError(f"Missing default target for {host}")
        assign(selection["bin"], platform)
        for target in selection["targets"]:
            resources = document["targets"][target]
            assign(resources["base"], platform)
            for optional in ("gui", "native", "profiling"):
                if optional in resources:
                    assign(resources[optional], platform)
    if locations.keys() != document["archives"].keys():
        raise ValueError("Manifest archives do not match the referenced components")
    for component, archive in document["archives"].items():
        filename = archive["path"]
        if not isinstance(filename, str) or "/" in filename or "\\" in filename:
            raise ValueError(f"Expected a generated archive filename for {component}")
        name(filename)
        if not isinstance(archive["size"], int) or archive["size"] <= 0:
            raise ValueError(f"Invalid archive size for {component}")
        if not re.fullmatch(r"[0-9a-f]{64}", archive["sha256"]):
            raise ValueError(f"Invalid archive digest for {component}")
        key = f"{release_dir}/{locations[component]}/{filename}"
        archive["path"] = base_url.rstrip("/") + "/" + quote(key, safe="/")
    return document


class R2:
    def __init__(self, work):
        required = (
            "SCOOP_RELEASE_R2_ENDPOINT",
            "SCOOP_RELEASE_R2_KEY_ID",
            "SCOOP_RELEASE_R2_SECRET",
        )
        for variable in required:
            if not os.environ.get(variable):
                raise ValueError(f"{variable} is not set")
        self.url = (
            os.environ[required[0]].rstrip("/")
            + "/"
            + os.environ.get("SCOOP_RELEASE_BUCKET", "scoop-releases")
        )
        self.auth = os.environ[required[1]] + ":" + os.environ[required[2]]
        self.work = work

    def request(self, key, source=None, immutable=False):
        response = self.work / "response"
        command = [
            "curl",
            "--silent",
            "--show-error",
            "--retry",
            "3",
            "--aws-sigv4",
            "aws:amz:auto:s3",
            "--user",
            self.auth,
            "--output",
            str(response),
            "--write-out",
            "%{http_code}",
        ]
        if source is not None:
            command.extend(
                [
                    "-X",
                    "PUT",
                    "--data-binary",
                    "@" + str(source),
                    "-H",
                    "Content-Type: application/toml; charset=utf-8",
                    "-H",
                    "Cache-Control: public, max-age="
                    + ("31536000, immutable" if immutable else "300"),
                ]
            )
            if immutable:
                command.extend(["-H", "If-None-Match: *"])
        command.append(self.url + "/" + quote(key, safe="/"))
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError(f"R2 request failed: {result.stderr.strip()}")
        return int(result.stdout), response.read_bytes()

    def upload(self, key, source, immutable=False):
        status, _ = self.request(key, source, immutable)
        if immutable and status == 412:
            status, existing = self.request(key)
            if status == 200 and existing == source.read_bytes():
                print(f"Reused {key}")
                return
            raise ValueError(
                f"{key} already identifies another build; use a new release version"
            )
        if not 200 <= status < 300:
            raise RuntimeError(f"Upload {key}: HTTP {status}")
        print(f"Uploaded {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest", type=Path, help="Complete manifest produced by Scoop packaging"
    )
    parser.add_argument(
        "--release-dir",
        required=True,
        help="R2 directory containing macos/, linux/ and windows/",
    )
    parser.add_argument("--base-url", default="https://release.scoop-lang.org")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "tmp/release-index")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Move latest.toml after publishing the fixed manifest",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write local output only; no credentials or network needed",
    )
    args = parser.parse_args()
    manifest = rewrite(
        tomllib.loads(args.manifest.read_text(encoding="utf-8")),
        args.release_dir,
        args.base_url,
    )
    key = f"versions/{manifest['version']}.toml"
    output = args.output_dir / key
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(toml_text(manifest), encoding="utf-8")
    latest = args.output_dir / "latest.toml"
    if args.latest:
        latest.write_text(
            toml_text({"schema": 1, "release": manifest["release"], "manifest": key}),
            encoding="utf-8",
        )
    print(f"Prepared {output} ({len(manifest['archives'])} components)")
    if args.dry_run:
        print("Dry run: nothing uploaded")
        return
    with tempfile.TemporaryDirectory(
        prefix="publish-", dir=args.output_dir
    ) as temporary:
        remote = R2(Path(temporary))
        remote.upload(key, output, immutable=True)
        if args.latest:
            remote.upload("latest.toml", latest)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, RuntimeError, OSError) as error:
        raise SystemExit(f"publish-release-index: {error}") from None
