# 出处:人工构造(CWE-918 aiohttp ClientSession 用户可控 URL)
async with aiohttp.ClientSession() as s:
    async with s.get(target_url) as resp:
        body = await resp.text()
