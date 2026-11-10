#!/bin/sh
# Bootstrap scoop-install, then pass toolchain installation options unchanged.
set -eu

scoop_error() { printf 'Error: %s\n' "$*" >&2; exit 1; }

scoop_quote() {
    printf "'"
    printf '%s' "$1" | sed "s/'/'\\\\''/g"
    printf "'"
}

scoop_add_path() {
    mkdir -p "$(dirname "$1")"
    if [ ! -f "$1" ] || ! grep -Fqx "$2" "$1"; then
        printf '\n# Scoop programming language\n%s\n' "$2" >> "$1"
        printf 'Updated %s\n' "$1"
    fi
}

scoop_install() {
    scoop_install_root=${SCOOP_HOME:-${HOME:?HOME must be set}/.scoop}
    scoop_next_home=false
    for scoop_arg do
        if [ "$scoop_next_home" = true ]; then
            scoop_install_root=$scoop_arg
            scoop_next_home=false
            continue
        fi
        case "$scoop_arg" in
            --home) scoop_next_home=true ;;
            --home=*) scoop_install_root=${scoop_arg#--home=} ;;
            -h|--help)
                printf '%s\n' \
                    'Usage: sh install.sh [VERSION] [--target TARGET] [--component gui,vendor] [--skip-docs] [--home DIR]' \
                    'Bootstrap scoop-install and install a toolchain (latest and the native target by default).' \
                    'All arguments are passed to: scoop-install toolchain install' \
                    'Set SCOOP_NO_MODIFY_PATH=1 to leave shell configuration unchanged.'
                return 0
                ;;
        esac
    done
    [ "$scoop_next_home" = false ] && [ -n "$scoop_install_root" ] || scoop_error '--home requires a directory'
    for scoop_command in curl mktemp; do
        command -v "$scoop_command" >/dev/null 2>&1 || scoop_error "$scoop_command is required"
    done
    scoop_system=$(uname -s)
    scoop_machine=$(uname -m)
    case "$scoop_system/$scoop_machine" in
        Darwin/arm64|Darwin/aarch64) scoop_host=aarch64-apple-darwin ;;
        Darwin/x86_64)
            [ "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" = 1 ] || \
                scoop_error 'the macOS release requires Apple Silicon'
            scoop_host=aarch64-apple-darwin
            ;;
        Linux/x86_64|Linux/amd64) scoop_host=x86_64-unknown-linux-gnu ;;
        MINGW*|MSYS*|CYGWIN*) scoop_error 'on Windows run: irm https://scoop-lang.org/install.ps1 | iex' ;;
        *) scoop_error "unsupported host: $scoop_system/$scoop_machine" ;;
    esac
    case "$scoop_install_root" in /*) ;; *) scoop_install_root=$PWD/$scoop_install_root ;; esac
    mkdir -p "$scoop_install_root/tmp"
    scoop_install_root=$(CDPATH= cd "$scoop_install_root" && pwd -P)
    scoop_download_dir=$(mktemp -d "$scoop_install_root/tmp/bootstrap.XXXXXX")
    trap 'rm -rf "$scoop_download_dir"' 0
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
    scoop_url=${SCOOP_INSTALL_URL:-https://github.com/scoop-lang/scoop-install/releases/latest/download/scoop-install-$scoop_host}
    printf 'Downloading scoop-install for %s...\n' "$scoop_host"
    curl -fSL --retry 3 "$scoop_url" -o "$scoop_download_dir/scoop-install"
    chmod +x "$scoop_download_dir/scoop-install"
    SCOOP_HOME=$scoop_install_root "$scoop_download_dir/scoop-install" toolchain install "$@"

    scoop_bin=$scoop_install_root/bin
    scoop_quoted=$(scoop_quote "$scoop_bin")
    scoop_path_line="case \":\$PATH:\" in *\":\"${scoop_quoted}\":\"*) ;; *) export PATH=${scoop_quoted}:\"\$PATH\" ;; esac"
    if [ "${SCOOP_NO_MODIFY_PATH:-0}" != 1 ]; then
        scoop_shell=${SHELL:-sh}
        case "${scoop_shell##*/}" in
            zsh) scoop_add_path "${ZDOTDIR:-$HOME}/.zshrc" "$scoop_path_line" ;;
            bash)
                scoop_add_path "$HOME/.bashrc" "$scoop_path_line"
                if [ -f "$HOME/.bash_profile" ]; then scoop_login_rc=$HOME/.bash_profile
                elif [ -f "$HOME/.bash_login" ]; then scoop_login_rc=$HOME/.bash_login
                else scoop_login_rc=$HOME/.profile; fi
                scoop_add_path "$scoop_login_rc" "$scoop_path_line"
                ;;
            fish) scoop_add_path "${XDG_CONFIG_HOME:-$HOME/.config}/fish/config.fish" "fish_add_path --path $scoop_quoted" ;;
            *) scoop_add_path "$HOME/.profile" "$scoop_path_line" ;;
        esac
    fi
    printf '\nScoop is installed in %s.\n' "$scoop_install_root"
    printf 'For this shell (sh, bash or zsh):\n  export PATH=%s:"$PATH"\n' "$scoop_quoted"
    printf 'Use scoop-install update to update while retaining your selected targets and components.\n'
}

# Keep execution last so curl | sh reads the entire script before downloading.
scoop_install "$@"
