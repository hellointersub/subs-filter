# fetch_and_convert.py
import aiohttp
import asyncio
import yaml
import base64
from urllib.parse import urlparse, parse_qs

async def fetch_base64(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

def parse_vless_url(link):
    try:
        url = urlparse(link)
        if url.scheme != "vless":
            return None

        uuid = url.netloc.split("@")[0]
        address = url.hostname
        port = url.port
        tag = url.fragment or f"{address}:{port}"

        params = parse_qs(url.query)
        config = {
            "type": "vless",
            "name": tag.replace(" ", "-"),
            "server": address,
            "port": port,
            "uuid": uuid,
            "tls": params.get("security", [""])[0] == "tls",
            "network": params.get("type", ["tcp"])[0]
        }

        if config["network"] == "ws":
            config["ws-opts"] = {}
            if "path" in params:
                config["ws-opts"]["path"] = params["path"][0]
            if "host" in params:
                config["ws-opts"]["headers"] = {"Host": params["host"][0]}

        return config
    except Exception as e:
        print("❌ Error parsing:", e)
        return None

async def main():
    url = "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/security/tls"
    raw_data = await fetch_base64(url)

    try:
        decoded = base64.b64decode(raw_data).decode("utf-8")
    except Exception as e:
        print("❌ Decode error:", e)
        return

    links = decoded.strip().splitlines()
    configs = [parse_vless_url(link.strip()) for link in links if link.strip().startswith("vless://")]
    configs = [c for c in configs if c]

    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(configs, f, allow_unicode=True)

    print(f"✅ Parsed {len(configs)} configs saved to config.yaml")

asyncio.run(main())
