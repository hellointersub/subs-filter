import aiohttp
import asyncio
import yaml
import base64
from urllib.parse import urlparse, parse_qs

async def fetch_base64(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            content = await resp.text()
            return content.strip()

def parse_link(link):
    try:
        o = urlparse(link)
        if o.scheme.lower() != "vless":
            return None
        params = parse_qs(o.query)
        uuid = o.netloc.split("@")[0]
        server = o.hostname
        port = o.port
        name = o.fragment or f"{server}-{port}"

        config = {
            "type": "vless",
            "name": name.replace(" ", "-"),
            "server": server,
            "port": port,
            "uuid": uuid,
            "tls": params.get("security", [""])[0] == "tls",
            "network": params.get("type", ["tcp"])[0],
        }

        if config["network"] == "ws":
            config["ws-opts"] = {}
            path = params.get("path", [""])[0]
            hosth = params.get("host", [""])[0]
            if path: config["ws-opts"]["path"] = path
            if hosth: config["ws-opts"].setdefault("headers", {})["Host"] = hosth

        return config
    except:
        return None

async def main():
    base64_url = "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/security/tls"
    content = await fetch_base64(base64_url)

    try:
        decoded = base64.b64decode(content).decode()
    except Exception as e:
        print("❌ Error decoding base64:", e)
        return

    links = [line.strip() for line in decoded.splitlines() if line.strip()]
    parsed = [parse_link(link) for link in links]
    valid = [x for x in parsed if x]

    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(valid, f, allow_unicode=True)

asyncio.run(main())
