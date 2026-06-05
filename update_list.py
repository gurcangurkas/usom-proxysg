import requests
import os
import re
import time

API_URL = "https://siberguvenlik.gov.tr/api/address/index"
OUTPUT_FILE = "usom_local_db.txt"

def clean_url(url_str):
    if not url_str:
        return ""
    url_str = url_str.replace('*', '')
    url_str = re.sub(r'^https?://', '', url_str, flags=re.IGNORECASE)
    url_str = re.sub(r'^ftp://', '', url_str, flags=re.IGNORECASE)
    url_str = url_str.split('?')[0]
    url_str = re.sub(r':[0-9]+', '', url_str)
    url_str = url_str.strip()
    if url_str.startswith('.'):
        url_str = url_str.lstrip('.')
    return url_str

def fetch_and_format_usom():
    try:
        proxysg_lines = ["define category USOM_Zararli_Siteler"]

        # API'den ilk sayfayı (0. sayfa) çekip toplam sayfa sayısını öğreniyoruz
        response = requests.get(API_URL, params={"page": 0}, timeout=30)
        response.raise_for_status()
        data = response.json()

        page_count = data.get("pageCount", 1)
        
        # Tüm sayfaları dönerek verileri topluyoruz
        for page in range(page_count):
            if page > 0:
                response = requests.get(API_URL, params={"page": page}, timeout=30)
                response.raise_for_status()
                data = response.json()
            
            # Dokümantasyondaki "models" dizisini alıyoruz
            models = data.get("models", [])
            for item in models:
                # API'nin url, domain veya value anahtarlarından hangisini döndürdüğünü yakalıyoruz
                addr_value = item.get('url') or item.get('domain') or item.get('value') or item.get('address', '')
                addr_type = str(item.get('type', '')).upper()
                
                # Sadece IP olmayanları alıp ProxySG kurallarına göre temizliyoruz
                if addr_value and "IP" not in addr_type:
                    cleaned = clean_url(addr_value)
                    if cleaned and len(cleaned) > 1:
                        proxysg_lines.append(f"  {cleaned}")
            
            # API'yi yormamak ve engellenmemek için sayfalar arası çok kısa bir bekleme
            time.sleep(0.1)

        # Mükerrer kayıtları temizleme ve bitirme
        unique_lines = [proxysg_lines[0]] + list(set(proxysg_lines[1:]))
        unique_lines.append("end")

        # Dosyayı Linux formatında oluşturma
        with open(OUTPUT_FILE, "w", newline="\n", encoding="utf-8") as f:
            f.write("\n".join(unique_lines))
            
        print(f"Başarılı! Toplam {page_count} sayfa tarandı ve {len(unique_lines) - 2} adet URL formatlandı.")

    except Exception as e:
        print(f"Sistem Hatası: {e}")
        # Hata durumunda işlemi kırmızı çarpı ile bitir ki eski txt dosyası silinmesin
        exit(1)

if __name__ == "__main__":
    fetch_and_format_usom()
