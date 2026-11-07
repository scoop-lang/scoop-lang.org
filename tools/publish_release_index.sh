#!/bin/sh
# Write the download index for a release in the scoop-releases R2 bucket.
#
# Usage: sh tools/publish_release_index.sh [--dry-run] [RELEASE]
#
# RELEASE is a top-level directory of the bucket such as 2026-11-07; the newest
# YYYY-MM-DD directory is used when it is omitted. The index is uploaded to
# RELEASE/index.txt and, unless RELEASE is older than the current latest, to
# latest.txt. Credentials come from the environment (see .envrc):
#   SCOOP_RELEASE_R2_KEY_ID, SCOOP_RELEASE_R2_SECRET, SCOOP_RELEASE_R2_ENDPOINT
#
# Index format (one record per line, fields separated by one space):
#   format 1
#   release <release directory>
#   version <toolchain version>
#   package <platform> <object key relative to https://release.scoop-lang.org/>
# Platforms are the bucket's directory names: macos, linux, windows.
set -eu

bucket=${SCOOP_RELEASE_BUCKET:-scoop-releases}
dry_run=false
release=

error() {
    printf 'publish-release-index: %s\n' "$*" >&2
    exit 1
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run) dry_run=true; shift ;;
        -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) error "unknown option: $1" ;;
        *) [ -z "$release" ] || error 'only one release may be given'; release=$1; shift ;;
    esac
done

for name in SCOOP_RELEASE_R2_KEY_ID SCOOP_RELEASE_R2_SECRET SCOOP_RELEASE_R2_ENDPOINT; do
    eval "value=\${$name:-}"
    [ -n "$value" ] || error "$name is not set (run direnv allow or source .envrc)"
done
endpoint=${SCOOP_RELEASE_R2_ENDPOINT%/}

r2() {
    curl -fsS --retry 3 --aws-sigv4 'aws:amz:auto:s3' \
        --user "$SCOOP_RELEASE_R2_KEY_ID:$SCOOP_RELEASE_R2_SECRET" "$@"
}

work=$(mktemp -d "${TMPDIR:-/tmp}/scoop-index.XXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' TERM

# List every object key, following continuation tokens.
: > "$work/keys"
token=
while :; do
    if [ -n "$token" ]; then
        r2 -G "$endpoint/$bucket" --data 'list-type=2' --data-urlencode "continuation-token=$token" \
            -o "$work/page.xml"
    else
        r2 -G "$endpoint/$bucket" --data 'list-type=2' -o "$work/page.xml"
    fi
    tr -d '\n' < "$work/page.xml" | grep -o '<Key>[^<]*</Key>' | sed 's#</*Key>##g' >> "$work/keys" || true
    tr -d '\n' < "$work/page.xml" | grep -q '<IsTruncated>true</IsTruncated>' || break
    token=$(tr -d '\n' < "$work/page.xml" | sed -n 's#.*<NextContinuationToken>\([^<]*\)</NextContinuationToken>.*#\1#p')
    [ -n "$token" ] || error 'listing is truncated but has no continuation token'
done

newest=$(sed -n 's#^\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)/.*#\1#p' "$work/keys" | sort -u | tail -n 1)
[ -n "$release" ] || release=$newest
[ -n "$release" ] || error 'the bucket contains no release directory'
case "$release" in
    *[!A-Za-z0-9._-]*|.*) error "invalid release name: $release" ;;
esac

{
    printf 'format 1\nrelease %s\n' "$release"
    version=
    found=false
    for platform in macos linux windows; do
        # The LLVM source archive is only needed to rebuild LLVM; the installer skips it.
        packages=$(grep "^$release/$platform/[^/]*\\.tar\\.xz\$" "$work/keys" | grep -v -- '-llvm-sources\.tar\.xz$' | sort || true)
        if [ -z "$packages" ]; then
            printf 'publish-release-index: %s has no %s packages\n' "$release" "$platform" >&2
            continue
        fi
        bin=$(printf '%s\n' "$packages" | grep -- '-bin-' | head -n 1 || true)
        if [ -z "$bin" ]; then
            printf 'publish-release-index: %s/%s has no bin package; skipping it\n' "$release" "$platform" >&2
            continue
        fi
        platform_version=$(printf '%s\n' "${bin##*/}" | sed -n 's#^scoop-\(.*\)-bin-.*\.tar\.xz$#\1#p')
        if [ -z "$version" ]; then
            version=$platform_version
            printf 'version %s\n' "$version"
        elif [ "$version" != "$platform_version" ]; then
            error "$platform packages are version $platform_version, expected $version"
        fi
        # The bin package carries post-install.sh, so list it first.
        printf 'package %s %s\n' "$platform" "$bin"
        printf '%s\n' "$packages" | grep -vFx -- "$bin" | sed "s#^#package $platform #"
        found=true
    done
    [ "$found" = true ] || error "$release has no installable packages"
} > "$work/index.txt"

cat "$work/index.txt"
if [ "$dry_run" = true ]; then
    printf '\n(dry run: nothing uploaded)\n'
    exit 0
fi

upload() {
    r2 -X PUT -H 'Content-Type: text/plain; charset=utf-8' -H "Cache-Control: $2" \
        --data-binary "@$work/index.txt" "$endpoint/$bucket/$1" -o /dev/null
    printf 'Uploaded %s\n' "$1"
}
upload "$release/index.txt" 'public, max-age=3600'
if [ "$(printf '%s\n%s\n' "$release" "$newest" | sort | tail -n 1)" = "$release" ]; then
    upload latest.txt 'public, max-age=300'
else
    printf 'Kept latest.txt: %s is older than %s\n' "$release" "$newest"
fi
