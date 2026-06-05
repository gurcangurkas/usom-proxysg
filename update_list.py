import requests
import os
import re

API_URL = "https://siberguvenlik.gov.tr/api/address/index"
OUTPUT_FILE = "usom_local_db.txt"

def clean_url(url_str):
    url_str = re.sub(r'^https?://', '', url_str, flags=re.IGNORECASE)
    url_str = re.sub(r'^ftp://', '', url_str, flags=re.IGNORECASE)
    url_str = url_str.split('?')[0]
    url_str = re.sub(r':[0-9]+', '', url_str)
    return url_str.strip()

def fetch_and_format_usom():
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        addresses = data if isinstance(data, list) else data.get('data', [])
        
        if not addresses:
            print("API'den boş veri döndü. Mevcut liste korunuyor.")
            return

        proxysg_lines = []
        proxysg_lines.append("define category USOM_Zararli_Siteler")

        for item in addresses:
            addr_value = item.get('value', '').strip()
            addr_type = item.get('type', '')
            
            if addr_value and "IP" not in str(addr_type).upper():
                cleaned = clean_url(addr_value)
                if cleaned:
                    proxysg_lines.append(f"  {cleaned}")

        unique_lines = [proxysg_lines[0]] + list(set(proxysg_lines[1:]))
        unique_lines.append("end")

        with open(OUTPUT_FILE, "w", newline="\n", encoding="utf-8") as f:
            f.write("\n".join(unique_lines))
            
        print(f"Başarılı! {len(unique_lines) - 2} adet URL temizlenerek formatlandı.")

    except Exception as e:
        print(f"Hata oluştu, işlem iptal edildi: {e}")
        exit(1)

if __name__ == "__main__":
    fetch_and_format_usom()
