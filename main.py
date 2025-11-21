import requests
import tweepy
import time
import urllib3
import os
import json # JSON kütüphanesini ekledik

# SSL hatalarını görmezden gel
urllib3.disable_warnings()

# ==========================================
# 1. AYARLAR (TWITTER ŞİFRELERİNİ GİR)
# ==========================================
# PC'de denerken os.environ.get yerine şifrelerinizi tırnak içinde yazın.
API_KEY = os.environ.get("TWITTER_API_KEY") 
API_SECRET = os.environ.get("TWITTER_API_SECRET")
ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET")

# ==========================================
# 2. AKILLI VERİ AJANI
# ==========================================
def fiyatlari_getir():
    print("📡 Opet veritabanına bağlanılıyor...")
    
    url = "https://api.opet.com.tr/api/fuelprices/prices?ProvinceCode=34&IncludeAllProducts=true"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.opet.com.tr/"
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status() # HTTP hatalarını yakalamak için
        data = response.json()
        
        bulunan_fiyatlar = {}
        hedef_ilceler = ["KADIKOY", "UMRANIYE", "ATASEHIR", "USKUDAR", "MALTEPE"]
        
        print(f"🔍 Toplam {len(data)} ilçe taraniyor...")

        # Tüm ilçeleri gez
        for ilce in data:
            ilce_adi = ilce.get("districtName", "").upper()
            
            # Verileri geçici olarak topla
            temp_fiyat = {"Benzin": None, "Motorin": None, "LPG": None}
            
            for urun in ilce.get("prices", []):
                isim = urun.get("productName", "")
                fiyat = urun.get("amount", 0)
                
                if "Kurşunsuz" in isim:
                    temp_fiyat["Benzin"] = fiyat
                elif "Motorin UltraForce" in isim:
                    temp_fiyat["Motorin"] = fiyat
                elif "Otogaz" in isim or "LPG" in isim:
                    temp_fiyat["LPG"] = fiyat
            
            # KURAL 1: Hedef ilçeyi bul ve hemen al!
            if ilce_adi in hedef_ilceler:
                print(f"✅ HEDEF İLÇE BULUNDU: {ilce_adi}")
                if temp_fiyat["LPG"] is None: temp_fiyat["LPG"] = "---"
                return temp_fiyat
            
            # KURAL 2: Hedef değilse bile, Benzin ve Motorin varsa kenarda tut (Yedek)
            if temp_fiyat["Benzin"] and temp_fiyat["Motorin"]:
                if not bulunan_fiyatlar:
                    print(f"ℹ️ Yedek olarak {ilce_adi} tutuluyor...")
                    bulunan_fiyatlar = temp_fiyat

        # Döngü bitti, hedef ilçe bulamadıysak yedeği döndür
        if bulunan_fiyatlar:
            if bulunan_fiyatlar["LPG"] is None: bulunan_fiyatlar["LPG"] = "---"
            return bulunan_fiyatlar
        
        return None

    except requests.exceptions.HTTPError as errh:
        print(f"❌ HTTP Hatası: {errh}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"❌ Bağlantı Hatası: {err}")
        return None
    except Exception as e:
        print(f"❌ Genel Hata: {e}")
        return None

# ==========================================
# 3. TWEET MOTORU
# ==========================================
def tweet_at(fiyatlar):
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET
        )
        
        # Test ederken spam hatası almamak için zaman damgası ekliyoruz
        tweet = f"""⛽ GÜNCEL AKARYAKIT FİYATLARI 🇹🇷

Benzi̇n:  {fiyatlar['Benzin']} TL
Motori̇n: {fiyatlar['Motorin']} TL
LPG:     {fiyatlar['LPG']} TL

📍 Kaynak: Opet (İst. Anadolu)
📅 Tarih: {time.strftime("%d.%m.%Y - %H:%M")}

#akaryakıt #benzin #motorin #lpg #zam #indirim
#TEST{int(time.time())}
"""

        client.create_tweet(text=tweet)
        print("🚀 BAŞARILI! Tweet atıldı.")
        
    except Exception as e:
        print(f"❌ Tweet atarken hata: {e}")

# ==========================================
# 4. BAŞLAT (PC MODU)
# ==========================================
if __name__ == "__main__":
    veriler = fiyatlari_getir()
    
    if veriler:
        print(f"\n💰 Çekilen Veriler: {veriler}")
        
        # 🟢 JSON kaydı (reply bot için)
        try:
            with open('last_prices.json', 'w', encoding='utf-8') as f:
                json.dump(veriler, f, ensure_ascii=False, indent=4)
            print("✅ Fiyatlar last_prices.json dosyasına kaydedildi.")
        except Exception as e:
            print(f"❌ JSON kaydetme hatası: {e}")
        
        # PC'de manuel onay al
        try:
            soru = input("\nTweet atmayı denemek ister misin? (e/h): ")
            if soru.lower() == "e":
                tweet_at(veriler)
            else:
                print("İptal edildi.")
        except EOFError:
            # GitHub Actions bu bloktan çalışır ve klavye girişi sormadan devam eder
            print("GitHub Actions ortamı tespit edildi. Otomatik tweet atılıyor...")
            tweet_at(veriler)
            
    else:
        print("❌ Uygun veri bulunamadı.")
