import subprocess
import sys
import os
import yaml
import requests
import tempfile
import asyncio
import aiohttp

SUBS_LINKS = [
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/security/tls"
]

OUTPUT_FILE = "best_sub.yaml"
MAX_SELECTED = 200

async def fetch(session, url):
    async with session.get(url) as resp:
        return await resp.text()

async def download_subs():
    async with aiohttp.ClientSession() as session:
        subs_texts = await asyncio.gather(*(fetch(session, url) for url in SUBS_LINKS))
    return subs_texts

def parse_clash_subs(text):
    # فرض می‌گیریم متن یک YAML clash است یا لینک‌هایی base64 شده هستند
    try:
        data = yaml.safe_load(text)
        # اگه keys مانند proxies داشته باشه کانفیگ‌ها رو برمی‌گردونه
        if isinstance(data, dict) and "proxies" in data:
            return data["proxies"]
    except Exception:
        pass

    # اگر YAML نبود، احتمالا سابسکرایپشن Base64 هست که باید decode کنیم
    import base64
    try:
        decoded = base64.b64decode(text).decode()
        data = yaml.safe_load(decoded)
        if isinstance(data, dict) and "proxies" in data:
            return data["proxies"]
    except Exception:
        pass

    # به عنوان fallback خط به خط کانفیگ‌ها رو برگردون
    lines = text.splitlines()
    proxies = [line.strip() for line in lines if line.strip()]
    return proxies

async def test_latency(proxy_url):
    # این قسمت نیاز به برنامه CLI هیدیفای یا sing-box داره که تست پینگ بگیره
    # برای سادگی اینجا فرض می‌کنیم delay رو 50 می‌ذاریم (باید جایگزین کنی با تست واقعی)
    # TODO: این بخش رو با اجرای CLI تست جایگزین کن
    import random
    delay = random.randint(20, 150)
    return delay

async def main():
    print("Downloading subscriptions...")
    subs_texts = await download_subs()
    all_proxies = []
    for sub_text in subs_texts:
        proxies = parse_clash_subs(sub_text)
        all_proxies.extend(proxies)

    print(f"Total proxies found: {len(all_proxies)}")
    # حالا برای هر proxy تست سرعت (latency) می‌گیریم
    print("Testing latency for proxies (simulated)...")
    delays = []
    for proxy in all_proxies:
        # اگر proxy یک دیکشنری بود، url رو چک می‌کنیم، وگرنه خط خام
        if isinstance(proxy, dict):
            # فرض بر این است که proxy dict نام دارد
            name = proxy.get("name", "")
            url = proxy.get("server", "")  # ممکنه url مستقیم نباشه، باید بر اساس ساختار تغییر کنه
            # ما فرض می‌کنیم url یا نوع کانفیگ لازم رو داریم
            delay = await test_latency(name)
            delays.append((delay, proxy))
        else:
            delay = await test_latency(proxy)
            delays.append((delay, proxy))

    # مرتب‌سازی بر اساس کمترین تاخیر
    delays.sort(key=lambda x: x[0])
    # انتخاب برترین‌ها
    selected = [p for _, p in delays[:MAX_SELECTED]]

    # ساخت خروجی clash YAML
    output_yaml = {
        "proxies": selected,
        "proxy-groups": [
            {
                "name": "Best 200",
                "type": "select",
                "proxies": [p["name"] if isinstance(p, dict) else str(p) for p in selected]
            }
        ],
        "rules": [
            "FINAL,Best 200"
        ]
    }
    print(f"Writing output file with {len(selected)} proxies...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(output_yaml, f, allow_unicode=True)

    print(f"Output saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
