# 出处:人工构造(依据 CWE-918 aiohttp 异步抓取形态)
async def mirror(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()
