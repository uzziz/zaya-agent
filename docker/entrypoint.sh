#!/bin/bash
# Docker/Podman entrypoint: bootstrap config files into the mounted volume, then run zaya.
set -e

ZAYA_HOME="${ZAYA_HOME:-/opt/data}"
INSTALL_DIR="/opt/zaya"

# --- Privilege dropping via gosu ---
# When started as root (the default for Docker, or fakeroot in rootless Podman),
# optionally remap the zaya user/group to match host-side ownership, fix volume
# permissions, then re-exec as zaya.
if [ "$(id -u)" = "0" ]; then
    if [ -n "$ZAYA_UID" ] && [ "$ZAYA_UID" != "$(id -u zaya)" ]; then
        echo "Changing zaya UID to $ZAYA_UID"
        usermod -u "$ZAYA_UID" zaya
    fi

    if [ -n "$ZAYA_GID" ] && [ "$ZAYA_GID" != "$(id -g zaya)" ]; then
        echo "Changing zaya GID to $ZAYA_GID"
        # -o allows non-unique GID (e.g. macOS GID 20 "staff" may already exist
        # as "dialout" in the Debian-based container image)
        groupmod -o -g "$ZAYA_GID" zaya 2>/dev/null || true
    fi

    actual_zaya_uid=$(id -u zaya)
    if [ "$(stat -c %u "$ZAYA_HOME" 2>/dev/null)" != "$actual_zaya_uid" ]; then
        echo "$ZAYA_HOME is not owned by $actual_zaya_uid, fixing"
        # In rootless Podman the container's "root" is mapped to an unprivileged
        # host UID — chown will fail.  That's fine: the volume is already owned
        # by the mapped user on the host side.
        chown -R zaya:zaya "$ZAYA_HOME" 2>/dev/null || \
            echo "Warning: chown failed (rootless container?) — continuing anyway"
    fi

    echo "Dropping root privileges"
    exec gosu zaya "$0" "$@"
fi

# --- Running as zaya from here ---
source "${INSTALL_DIR}/.venv/bin/activate"

# Create essential directory structure.  Cache and platform directories
# (cache/images, cache/audio, platforms/whatsapp, etc.) are created on
# demand by the application — don't pre-create them here so new installs
# get the consolidated layout from get_zaya_dir().
# The "home/" subdirectory is a per-profile HOME for subprocesses (git,
# ssh, gh, npm …).  Without it those tools write to /root which is
# ephemeral and shared across profiles.  See issue #4426.
mkdir -p "$ZAYA_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# .env
if [ ! -f "$ZAYA_HOME/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$ZAYA_HOME/.env"
fi

# config.yaml
if [ ! -f "$ZAYA_HOME/config.yaml" ]; then
    cp "$INSTALL_DIR/cli-config.yaml.example" "$ZAYA_HOME/config.yaml"
fi

# SOUL.md
if [ ! -f "$ZAYA_HOME/SOUL.md" ]; then
    cp "$INSTALL_DIR/docker/SOUL.md" "$ZAYA_HOME/SOUL.md"
fi

# Sync bundled skills (manifest-based so user edits are preserved)
if [ -d "$INSTALL_DIR/skills" ]; then
    python3 "$INSTALL_DIR/tools/skills_sync.py"
fi

exec zaya "$@"
