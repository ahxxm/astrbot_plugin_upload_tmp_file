# astrbot_plugin_upload_tmp_file

[AstrBot](https://github.com/AstrBotDevs/AstrBot) plugin that automatically uploads large files to temporary hosting services when they exceed platform size limits.

## How it works

The plugin intercepts outgoing messages before they reach the platform. When a file attachment exceeds the platform's size limit, it uploads the file to a temporary hosting service and replaces the attachment with a download link.

- **litterbox.catbox.moe** (primary) — up to 1GB, 72h expiry
- **tmpfiles.org** (fallback) — up to 100MB, 60min expiry

## Platform size limits

| Platform | Threshold |
|---|---|
| Discord | 25 MB |
| Others (Telegram, QQ, etc.) | 50 MB |

## Installation

Install through AstrBot WebUI plugin management, or clone into `AstrBot/data/plugins/`:

```bash
cd AstrBot/data/plugins
git clone https://github.com/ahxxm/astrbot_plugin_upload_tmp_file
```
