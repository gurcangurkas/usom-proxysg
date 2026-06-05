import requests
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://siberguvenlik.gov.tr/api/address/index"
OUTPUT_FILE = "usom_local_db.txt"

def clean_url(url_str):
    if not url_str: return ""
    url_str = url_str.replace('*', '')
    url_str = re.sub(r'^https?://', '', url_str, flags=re.IGNORECASE)
    url_str = re.sub(r'^ftp://', '', url_str, flags=re.IGNORECASE)
    url_str = url_str.split('?')[0]
    url_str = re.sub(r':[0-9]+', '', url_str)
    url_str = url_str.strip()
    if url_str.startswith('.'): url_str = url_str.lstrip('.')
    return url_str

def fetch_page(session, addr_type, page):
    try:
        response = session.get(API_URL, params={"type": addr_type, "page": page}, timeout=20)
        response.raise_for_status()
        return response.json().get("models", [])
    except:
        return []

def fetch_and_format_usom():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20))
    
    proxysg_lines = ["define category USOM_Zararli_Siteler"]
    types_to_fetch = ['domain', 'url']
    
    # ProxySG'nin hata verdiği sorunlu karakterler
    invalid_chars = ['=', '&', '(', ')', '"', "'", ' ', ';', ',', '<', '>']
    
    for addr_type in types_to_fetch:
        print(f"\n--- '{addr_type.upper()}' tipi için veri çekimi başlatılıyor ---", flush=True)
        try:
            resp = session.get(API_URL, params={"type": addr_type, "page": 0}, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            page_count = data.get("pageCount", 1)
            total_count = data.get("totalCount", 0)
            
            print(f"Bulunan {addr_type.upper()} sayısı: {total_count} (Toplam {page_count} sayfa)", flush=True)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(fetch_page, session, addr_type, p): p for p in range(page_count)}
                
                completed = 0
                for future in as_completed(futures):
                    models = future.result()
                    for item in models:
                        url_val = item.get('url', '')
                        cleaned = clean_url(url_val)
                        
                        if cleaned and len(cleaned) > 1:
                            # İÇİNDE PROXYSG'Yİ BOZAN KARAKTER YOKSA LİSTEYE EKLE
                            if not any(char in cleaned for char in invalid_chars):
                                proxysg_lines.append(f"  {cleaned}")
                    
                    completed += 1
                    if completed % 500 == 0 or completed == page_count:
                        print(f"[{addr_type.upper()}] İşlenen sayfa: {completed}/{page_count}", flush=True)
                        
        except Exception as e:
            print(f"{addr_type.upper()} çekilirken kritik hata: {e}", flush=True)

    unique_lines = [proxysg_lines[0]] + list(set(proxysg_lines[1:]))
    unique_lines.append("end")

    with open(OUTPUT_FILE, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(unique_lines))
        
    print(f"\nİşlem Tamamlandı! Toplam {len(unique_lines) - 2} adet adres ProxySG formatında hazır.", flush=True)

if __name__ == "__main__":
    fetch_and_format_usom()
