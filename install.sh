#!/bin/sh
# Download and prepare the Scoop programming language toolchain.
set -eu

scoop_error() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

scoop_add_path() {
    scoop_rc=$1
    scoop_path_line=$2
    mkdir -p "$(dirname "$scoop_rc")"
    if [ ! -f "$scoop_rc" ] || ! grep -Fqx "$scoop_path_line" "$scoop_rc"; then
        printf '\n# Scoop programming language\n%s\n' "$scoop_path_line" >> "$scoop_rc"
        printf 'Updated %s\n' "$scoop_rc"
    fi
}

scoop_install() {
    scoop_release=
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --release|--version)
                [ "$#" -ge 2 ] || scoop_error "$1 requires a release name"
                scoop_release=$2
                shift 2
                ;;
            --)
                shift
                break
                ;;
            -h|--help)
                printf '%s\n' \
                    'Usage: sh install.sh [--release RELEASE] [-- POST_INSTALL_OPTIONS...]' \
                    'Install the latest Scoop release into ~/.scoop.' \
                    'RELEASE names a published release such as 2026-11-09 (--version is an alias).' \
                    'Examples:' \
                    '  curl -fsSL https://scoop-lang.org/install.sh | sh' \
                    '  sh install.sh --release 2026-11-09 -- --jobs 2' \
                    '  sh install.sh -- --all-targets'
                return 0
                ;;
            *) scoop_error "unknown option: $1 (use --help)" ;;
        esac
    done

    [ -n "${HOME:-}" ] || scoop_error 'HOME must be set'
    for scoop_command in curl tar mktemp; do
        command -v "$scoop_command" >/dev/null 2>&1 || scoop_error "$scoop_command is required"
    done
    scoop_system=$(uname -s)
    scoop_machine=$(uname -m)
    case "$scoop_system/$scoop_machine" in
        Darwin/arm64|Darwin/aarch64) scoop_platform=macos ;;
        Darwin/x86_64)
            [ "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" = 1 ] || \
                scoop_error 'the macOS release requires Apple Silicon'
            scoop_platform=macos
            ;;
        Linux/x86_64|Linux/amd64) scoop_platform=linux ;;
        MINGW*|MSYS*|CYGWIN*) scoop_platform=windows ;;
        *) scoop_error "unsupported host: $scoop_system/$scoop_machine" ;;
    esac

    scoop_base_url=${SCOOP_RELEASE_URL:-https://release.scoop-lang.org}
    scoop_base_url=${scoop_base_url%/}
    if [ -z "$scoop_release" ]; then
        scoop_index_url=$scoop_base_url/latest.txt
    else
        case "$scoop_release" in
            ''|.*|*[!A-Za-z0-9._-]*) scoop_error "invalid release name: $scoop_release" ;;
        esac
        scoop_index_url=$scoop_base_url/$scoop_release/index.txt
    fi

    scoop_download_dir=$(mktemp -d "${TMPDIR:-$HOME}/scoop-install.XXXXXX")
    trap 'rm -rf "$scoop_download_dir"' 0
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM

    curl -fsSL --retry 3 "$scoop_index_url" -o "$scoop_download_dir/index.txt" || \
        scoop_error "could not download the release index $scoop_index_url"
    scoop_format= scoop_index_release= scoop_version= scoop_packages= scoop_package_count=0
    while read -r scoop_kind scoop_field scoop_value scoop_rest || [ -n "${scoop_kind:-}" ]; do
        case "$scoop_kind" in
            format) scoop_format=$scoop_field ;;
            release) scoop_index_release=$scoop_field ;;
            version) scoop_version=$scoop_field ;;
            package)
                [ "$scoop_field" = "$scoop_platform" ] || continue
                case "$scoop_value" in
                    ''|/*|*..*|*[!A-Za-z0-9._/+-]*) scoop_error "release index lists an invalid package: $scoop_value" ;;
                esac
                scoop_packages="${scoop_packages:+$scoop_packages }$scoop_value"
                scoop_package_count=$((scoop_package_count + 1))
                ;;
        esac
    done < "$scoop_download_dir/index.txt"
    [ "$scoop_format" = 1 ] || scoop_error "unsupported release index format at $scoop_index_url"
    case "$scoop_version" in
        ''|*[!A-Za-z0-9.+-]*) scoop_error "release index has an invalid version: $scoop_version" ;;
    esac

    if [ -z "$scoop_packages" ]; then
        scoop_error "Scoop packages for $scoop_platform are not ready yet in release $scoop_index_release.
Please build Scoop from source: https://github.com/windoze/scoop"
    fi
    if [ "$scoop_platform" = windows ]; then
        printf 'Download these packages, extract them into %%USERPROFILE%%\\.scoop and run post-install.ps1:\n' >&2
        for scoop_package in $scoop_packages; do
            printf '  %s/%s\n' "$scoop_base_url" "$scoop_package" >&2
        done
        scoop_error 'this script cannot install on Windows; see https://scoop-lang.org/docs/install.html'
    fi

    printf 'Downloading Scoop %s (release %s) for %s...\n' "$scoop_version" "$scoop_index_release" "$scoop_platform"
    mkdir "$scoop_download_dir/package"
    scoop_package_number=0
    # Package keys contain no whitespace, so the list is split on spaces.
    for scoop_package in $scoop_packages; do
        scoop_package_number=$((scoop_package_number + 1))
        printf '[%s/%s] %s\n' "$scoop_package_number" "$scoop_package_count" "${scoop_package##*/}"
        curl -fSL --retry 3 "$scoop_base_url/$scoop_package" -o "$scoop_download_dir/archive.tar.xz"
        tar -xJf "$scoop_download_dir/archive.tar.xz" -C "$scoop_download_dir/package"
        rm -f "$scoop_download_dir/archive.tar.xz"
    done
    [ -f "$scoop_download_dir/package/post-install.sh" ] || scoop_error 'the release is missing post-install.sh'

    scoop_install_root=$HOME/.scoop
    mkdir -p "$scoop_install_root"
    # Replace distribution files so an upgrade cannot reuse an old target's slibs.
    # Keep package caches, build results and user-supplied external commands.
    for scoop_component in bin lib include src vendor native libexec docs share tooling; do
        rm -rf "${scoop_install_root:?}/${scoop_component:?}"
    done
    cp -Rp "$scoop_download_dir/package/." "$scoop_install_root/"
    # The lib packages carry prebuilt system libraries; post-install only writes the API docs.
    printf 'Generating API documentation...\n'
    if sh "$scoop_install_root/post-install.sh" "$@"; then
        "$scoop_install_root/bin/scoop" --version
    else
        scoop_exit=$?
        printf 'Installation preparation failed. Fix the reported error, then rerun:\n  sh "%s/post-install.sh"\n' \
            "$scoop_install_root" >&2
        return "$scoop_exit"
    fi

    # Expand the user's variables when the rc file is sourced.
    # shellcheck disable=SC2016
    scoop_path_line='case ":$PATH:" in *":$HOME/.scoop/bin:"*) ;; *) export PATH="$HOME/.scoop/bin:$PATH" ;; esac'
    scoop_shell=${SHELL:-sh}
    case "${scoop_shell##*/}" in
        zsh) scoop_add_path "${ZDOTDIR:-$HOME}/.zshrc" "$scoop_path_line" ;;
        bash)
            scoop_add_path "$HOME/.bashrc" "$scoop_path_line"
            if [ -f "$HOME/.bash_profile" ]; then
                scoop_login_rc=$HOME/.bash_profile
            elif [ -f "$HOME/.bash_login" ]; then
                scoop_login_rc=$HOME/.bash_login
            else
                scoop_login_rc=$HOME/.profile
            fi
            scoop_add_path "$scoop_login_rc" "$scoop_path_line"
            ;;
        fish)
            # shellcheck disable=SC2016
            scoop_add_path "${XDG_CONFIG_HOME:-$HOME/.config}/fish/config.fish" \
                'fish_add_path --path "$HOME/.scoop/bin"'
            ;;
        *) scoop_add_path "$HOME/.profile" "$scoop_path_line" ;;
    esac
    printf '\nScoop is installed in %s.\nOpen a new shell to use it.\n' "$scoop_install_root"
    # shellcheck disable=SC2016
    printf 'For this shell (sh, bash or zsh):\n  export PATH="$HOME/.scoop/bin:$PATH"\n'
}

# Keep execution at the end so curl | sh reads the whole script before installing.
scoop_install "$@"
