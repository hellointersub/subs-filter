import asyncio, aiohttp, yaml, re
from urllib.parse import urlparse, parse_qs

SUBS_LINK = "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/security/tls"
MAX_ITEMS = 200

def parse_link(link):
    o = urlparse(link)
    scheme = o.scheme.lower()
    info = {"type": scheme}
    if scheme == "vless":
        user, host = o.netloc.split("@")
        uuid = user
        server, port = host.split(":")
        info.update({
            "name": f"{server.replace('.', '-')}-{port}",
            "server": server,
            "port": int(port),
            "uuid": uuid
        })
        params = parse_qs(o.query)
        info["tls"] = params.get("security", [""])[0] == "tls"
        info["network"] = params.get("type", [""])[0]
        if info["network"] == "ws":
            info["ws-opts"] = {}
            path = params.get("path", [""])[0]
            hosth = params.get("host", [""])[0]
            if path: info["ws-opts"]["path"] = path
            if hosth: info["ws-opts"].setdefault("headers", {})["Host"] = hosth
    else:
        return None
    return info

async def main():
    async with aiohttp.ClientSession() as sess:
        text = await (await sess.get(SUBS_LINK)).text()
    links = [line.strip() for line in text.splitlines() if line.strip()]
    parsed = [parse_link(l) for l in links]
    parsed = [p for p in parsed if p is not None][:MAX_ITEMS]
    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, allow_unicode=True)

if __name__ == "__main__":
    asyncio.run(main())
