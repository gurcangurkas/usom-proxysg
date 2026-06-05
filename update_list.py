import requests
import os
import re

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
    # Bağlantı havuzu (Session) oluşturarak istekleri çok hızlandırıyoruz
    session = requests.Session()
    
    try:
        proxysg_lines = ["define category USOM_Zararli_Siteler"]

        print("USOM API'sine bağlanılıyor...")
        response = session.get(API_URL, params={"page": 0}, timeout=30)
        response.raise_for_status()
        data = response.json()

        # OpenAPI şemasından 'pageCount' değerini alıyoruz
        page_count = data.get("pageCount", 1)
        print(f"Toplam {page_count} sayfa veri tespit edildi. İndirme başlıyor...")
        
        for page in range(page_count):
            if page > 0:
                response = session.get(API_URL, params={"page": page}, timeout=30)
                response.raise_for_status()
                data = response.json()
            
            # OpenAPI şemasından 'models' dizisini alıyoruz
            models = data.get("models", [])
            for item in models:
                # Şemaya göre adres 'url', tür ise 'type' içinde dönüyor
                addr_value = item.get('url', '')
                addr_type = str(item.get('type', '')).lower()
                
                # ProxySG için ip, ip6 ve ip6net türlerini eliyoruz. Sadece domain ve url alıyoruz.
                if addr_value and addr_type in ['domain', 'url']:
                    cleaned = clean_url(addr_value)
                    if cleaned and len(cleaned) > 1:
                        proxysg_lines.append(f"  {cleaned}")
            
            # GitHub loglarında işlemin donmadığını görmek için her 50 sayfada bir bilgi basıyoruz
            if page % 50 == 0:
                print(f"İşlenen sayfa: {page}/{page_count}")

        unique_lines = [proxysg_lines[0]] + list(set(proxysg_lines[1:]))
        unique_lines.append("end")

        with open(OUTPUT_FILE, "w", newline="\n", encoding="utf-8") as f:
            f.write("\n".join(unique_lines))
            
        print(f"İşlem Tamamlandı! {len(unique_lines) - 2} adet adres ProxySG formatında kaydedildi.")

    except Exception as e:
        print(f"Sistem Hatası: {e}")
        exit(1)

if __name__ == "__main__":
    fetch_and_format_usom()
