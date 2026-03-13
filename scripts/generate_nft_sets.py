#!/usr/bin/env python3
import os
import requests
from pathlib import Path

# 配置
BASE_URL = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geopip/"
COUNTRIES = ["cn", "us", "jp", "de", "fr"]  # 根据需要修改
OUTPUT_DIR = Path("geoip-nft")

# 确保输出目录存在
OUTPUT_DIR.mkdir(exist_ok=True)

def download_list(country):
    url = f"{BASE_URL}{country}.list"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text.splitlines()
    except Exception as e:
        print(f"Failed to download {country}.list: {e}")
        return []

def generate_nft_set(country, cidrs):
    if not cidrs:
        return
    # 过滤空行和注释行（如果有）
    cidrs = [line.strip() for line in cidrs if line.strip() and not line.startswith('#')]
    if not cidrs:
        return

    content = f"""# Auto-generated from MetaCubeX/meta-rules-dat
# {country} IPv4 addresses

set {country}_ipv4 {{
    type ipv4_addr
    flags interval
    elements = {{
{', '.join(cidrs)}
    }}
}}
"""
    output_file = OUTPUT_DIR / f"{country}.nft"
    output_file.write_text(content)
    print(f"Generated {output_file} with {len(cidrs)} CIDRs")

def main():
    for country in COUNTRIES:
        print(f"Processing {country}...")
        cidrs = download_list(country)
        if cidrs:
            generate_nft_set(country, cidrs)

if __name__ == "__main__":
    main()
