"""
Shared platform registry for Zaya Agent.

Single source of truth for platform metadata consumed by both
skills_config (label display) and tools_config (default toolset
resolution).  Import ``PLATFORMS`` from here instead of maintaining
duplicate dicts in each module.
"""

from collections import OrderedDict
from typing import NamedTuple


class PlatformInfo(NamedTuple):
    """Metadata for a single platform entry."""
    label: str
    default_toolset: str


# Ordered so that TUI menus are deterministic.
PLATFORMS: OrderedDict[str, PlatformInfo] = OrderedDict([
    ("cli",            PlatformInfo(label="🖥️  CLI",            default_toolset="zaya-cli")),
    ("telegram",       PlatformInfo(label="📱 Telegram",        default_toolset="zaya-telegram")),
    ("discord",        PlatformInfo(label="💬 Discord",         default_toolset="zaya-discord")),
    ("slack",          PlatformInfo(label="💼 Slack",           default_toolset="zaya-slack")),
    ("whatsapp",       PlatformInfo(label="📱 WhatsApp",        default_toolset="zaya-whatsapp")),
    ("signal",         PlatformInfo(label="📡 Signal",          default_toolset="zaya-signal")),
    ("bluebubbles",    PlatformInfo(label="💙 BlueBubbles",     default_toolset="zaya-bluebubbles")),
    ("email",          PlatformInfo(label="📧 Email",           default_toolset="zaya-email")),
    ("homeassistant",  PlatformInfo(label="🏠 Home Assistant",  default_toolset="zaya-homeassistant")),
    ("mattermost",     PlatformInfo(label="💬 Mattermost",      default_toolset="zaya-mattermost")),
    ("matrix",         PlatformInfo(label="💬 Matrix",          default_toolset="zaya-matrix")),
    ("dingtalk",       PlatformInfo(label="💬 DingTalk",        default_toolset="zaya-dingtalk")),
    ("feishu",         PlatformInfo(label="🪽 Feishu",          default_toolset="zaya-feishu")),
    ("wecom",          PlatformInfo(label="💬 WeCom",           default_toolset="zaya-wecom")),
    ("wecom_callback", PlatformInfo(label="💬 WeCom Callback",  default_toolset="zaya-wecom-callback")),
    ("weixin",         PlatformInfo(label="💬 Weixin",          default_toolset="zaya-weixin")),
    ("qqbot",          PlatformInfo(label="💬 QQBot",           default_toolset="zaya-qqbot")),
    ("webhook",        PlatformInfo(label="🔗 Webhook",         default_toolset="zaya-webhook")),
    ("api_server",     PlatformInfo(label="🌐 API Server",      default_toolset="zaya-api-server")),
])


def platform_label(key: str, default: str = "") -> str:
    """Return the display label for a platform key, or *default*."""
    info = PLATFORMS.get(key)
    return info.label if info is not None else default
