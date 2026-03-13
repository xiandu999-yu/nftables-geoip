#!/usr/bin/env python3
import requests
from pathlib import Path
import ipaddress

# 配置
BASE_URL = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/"
COUNTRIES = ["cn", "us", "jp", "de", "fr"]  # 按需修改
OUTPUT_DIR = Path("geoip-nft")

OUTPUT_DIR.mkdir(exist_ok=True)

def download_list(country):
    """下载指定国家的 IP 列表文件"""
    url = f"{BASE_URL}{country}.list"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        # 按行分割，过滤空行和以 '#' 开头的注释行
        lines = [line.strip() for line in r.text.splitlines()
                 if line.strip() and not line.startswith('#')]
        return lines
    except Exception as e:
        print(f"下载 {url} 失败: {e}")
        return []

def validate_and_split_cidrs(cidr_strings):
    """验证 CIDR 并分离为 IPv4 和 IPv6 列表"""
    ipv4_cidrs = []
    ipv6_cidrs = []
    for cidr in cidr_strings:
        try:
            # 解析网络，strict=False 允许非严格格式（如主机位不为0）
            net = ipaddress.ip_network(cidr, strict=False)
            if net.version == 4:
                ipv4_cidrs.append(str(net))
            else:  # version == 6
                ipv6_cidrs.append(str(net))
        except ValueError as e:
            print(f"警告: 忽略无效 CIDR '{cidr}' - {e}")
    return ipv4_cidrs, ipv6_cidrs

def generate_nft_file(country, cidrs, version):
    """生成 nftables 集合文件"""
    if not cidrs:
        return

    set_name = f"{country}_ipv{version}"
    addr_type = f"ipv{version}_addr"

    # 格式化：每个 CIDR 一行，带缩进，末尾加逗号
    elements_str = ",\n".join(f"    {cidr}" for cidr in cidrs)

    content = f"""# Auto-generated from MetaCubeX/meta-rules-dat
# {country} IPv{version} addresses

set {set_name} {{
    type {addr_type}
    flags interval
    elements = {{
{elements_str}
    }}
}}
"""
    output_file = OUTPUT_DIR / f"{country}_v{version}.nft"
    output_file.write_text(content)
    print(f"生成 {output_file}，包含 {len(cidrs)} 个 IPv{version} 地址段")

def main():
    for country in COUNTRIES:
        print(f"\n处理 {country}...")
        raw_lines = download_list(country)
        if not raw_lines:
            continue

        ipv4_list, ipv6_list = validate_and_split_cidrs(raw_lines)

        if ipv4_list:
            generate_nft_file(country, ipv4_list, 4)
        if ipv6_list:
            generate_nft_file(country, ipv6_list, 6)

        print(f"{country}: 发现 IPv4 {len(ipv4_list)} 条, IPv6 {len(ipv6_list)} 条")

if __name__ == "__main__":
    main()
