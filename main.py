import os
import re
from pathlib import Path

import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import File, Plain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

LITTERBOX_ENDPOINT = "https://litterbox.catbox.moe/resources/internals/api.php"
TMPFILES_ENDPOINT = "https://tmpfiles.org/api/v1/upload"

MB = 1024 * 1024
DEFAULT_FILE_SIZE_THRESHOLD = 50 * MB
PLATFORM_FILE_SIZE_THRESHOLD = {
    "discord": 25 * MB,
}


async def upload_to_litterbox(file_path: str, expiry: str = "24h") -> str:
    """Upload a file to litterbox.catbox.moe. Returns direct download URL."""
    path = Path(file_path)
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        form.add_field("reqtype", "fileupload")
        form.add_field("time", expiry)
        with path.open("rb") as f:
            form.add_field("fileToUpload", f, filename=path.name)
            async with session.post(LITTERBOX_ENDPOINT, data=form) as resp:
                resp.raise_for_status()
                return (await resp.text()).strip()


async def upload_to_tmpfiles(file_path: str) -> str:
    """Upload a file to tmpfiles.org. Returns direct download URL."""
    path = Path(file_path)
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        with path.open("rb") as f:
            form.add_field("file", f, filename=path.name)
            async with session.post(TMPFILES_ENDPOINT, data=form) as resp:
                resp.raise_for_status()
                data = await resp.json()
    if data.get("status") != "success":
        raise RuntimeError(f"tmpfiles.org upload failed: {data}")
    page_url = data["data"]["url"]
    return re.sub(r"(tmpfiles\.org)/", r"\1/dl/", page_url, count=1)


async def upload_file(file_path: str, expiry: str = "24h") -> str:
    """Try litterbox first, fall back to tmpfiles.org."""
    try:
        url = await upload_to_litterbox(file_path, expiry)
        logger.info(f"Uploaded to litterbox: {url}")
        return url
    except Exception as e:
        logger.warning(f"Litterbox upload failed: {e}, falling back to tmpfiles.org")
    url = await upload_to_tmpfiles(file_path)
    logger.info(f"Uploaded to tmpfiles: {url}")
    return url


@register("upload_tmp_file", "ahxxm", "上传文件到临时文件托管服务", "0.1.0")
class UploadTmpFilePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.on_decorating_result()
    async def intercept_large_files(self, event: AstrMessageEvent):
        result = event.get_result()
        if result is None:
            return
        platform = event.get_platform_name()
        threshold = PLATFORM_FILE_SIZE_THRESHOLD.get(platform, DEFAULT_FILE_SIZE_THRESHOLD)
        chain = result.chain
        for i, comp in enumerate(chain):
            if not isinstance(comp, File):
                continue
            local_path = await comp.get_file()
            if not local_path or not os.path.exists(local_path):
                continue
            size = os.path.getsize(local_path)
            if size <= threshold:
                continue
            logger.info(f"File {comp.name} is {size} bytes, uploading to temp hosting")
            try:
                url = await upload_file(local_path)
                chain[i] = Plain(f"[文件] {comp.name}\n{url}")
            except Exception as e:
                logger.error(f"Failed to upload {comp.name}: {e}")
