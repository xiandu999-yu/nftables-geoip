#!/usr/bin/env python3
import os
import requests
from pathlib import Path
import ipaddress  # 用于验证 CIDR 格式

# 配置
BASE_URL_V4 = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/"
BASE_URL_V6 = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/ipv6/"  # 需确认路径
COUNTRIES = ["cn", "us", "jp", "de", "fr"]  # 根据需要修改
OUTPUT_DIR = Path("geoip-nft")

OUTPUT_DIR.mkdir(exist_ok=True)

def download_list(country, version='v4'):
    """下载指定国家的 IP 列表，version 为 'v4' 或 'v6'"""
    if version == 'v4':
        base = BASE_URL_V4
        suffix = ".list"
    else:
        base = BASE_URL_V6
        suffix = "6.list"  # 假设 IPv6 文件名为 cn6.list，需确认
    
    url = f"{base}{country}{suffix}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        # 按行分割，过滤空行和注释行（以 # 开头）
        lines = [line.strip() for line in r.text.splitlines() 
                 if line.strip() and not line.startswith('#')]
        # 可选：验证 CIDR 格式
        valid_cidrs = []
        for cidr in lines:
            try:
                ipaddress.ip_network(cidr, strict=False)
                valid_cidrs.append(cidr)
            except ValueError:
                print(f"警告: 忽略无效 CIDR {cidr} in {country}{suffix}")
        return valid_cidrs
    except Exception as e:
        print(f"下载 {url} 失败: {e}")
        return []

def generate_nft_set(country, cidrs, version='v4'):
    """生成 nftables 集合文件"""
    if not cidrs:
        return
    
    # 确定集合名称和类型
    if version == 'v4':
        set_name = f"{country}_ipv4"
        addr_type = "ipv4_addr"
    else:
        set_name = f"{country}_ipv6"
        addr_type = "ipv6_addr"
    
    # 格式化 CIDR 列表：每个占一行，末尾加逗号
    elements_str = ",\n".join(f"    {cidr}" for cidr in cidrs)
    
    content = f"""# Auto-generated from MetaCubeX/meta-rules-dat
# {country} IPv{version[-1]} addresses

set {set_name} {{
    type {addr_type}
    flags interval
    elements = {{
{elements_str}
    }}
}}
"""
    output_file = OUTPUT_DIR / f"{country}_{version}.nft"
    output_file.write_text(content)
    print(f"生成 {output_file}，包含 {len(cidrs)} 个 CIDR")

def main():
    for country in COUNTRIES:
        print(f"处理 {country} IPv4...")
        cidrs_v4 = download_list(country, 'v4')
        if cidrs_v4:
            generate_nft_set(country, cidrs_v4, 'v4')
        
        # 尝试下载 IPv6（如果仓库中有对应文件）
        print(f"处理 {country} IPv6...")
        cidrs_v6 = download_list(country, 'v6')
        if cidrs_v6:
            generate_nft_set(country, cidrs_v6, 'v6')
        else:
            print(f"{country} 没有 IPv6 列表或下载失败")

if __name__ == "__main__":
    main()
