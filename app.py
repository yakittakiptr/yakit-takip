import requests
import tweepy
import time
import urllib3
import os

# SSL hatalarını görmezden gel
urllib3.disable_warnings()

# ==========================================
# 1. AYARLAR (TWITTER ŞİFRELERİNİ GİR)
# ==========================================
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
        data = response.json()
        
        bulunan_fiyatlar = {}
        hedef_ilceler = ["KADIKOY", "UMRANIYE", "ATASEHIR", "USKUDAR", "MALTEPE"]
        
        print(f"🔍 Toplam {len(data)} ilçe taraniyor...")

        # Tüm ilçeleri gez
        for ilce in data:
            ilce_adi = ilce.get("districtName", "").upper() # Büyük harfe çevir
            
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
            
            # KURAL 1: Eğer bu ilçe Bizim Hedef Listede ise (Kadıköy vb.) hemen al!
            if ilce_adi in hedef_ilceler:
                print(f"✅ HEDEF İLÇE BULUNDU: {ilce_adi}")
                # LPG yoksa 'Veri Yok' yazmasın diye kontrol
                if temp_fiyat["LPG"] is None: temp_fiyat["LPG"] = "---"
                return temp_fiyat
            
            # KURAL 2: Hedef değilse bile, Benzin ve Motorin varsa kenarda tut (Yedek)
            if temp_fiyat["Benzin"] and temp_fiyat["Motorin"]:
                if not bulunan_fiyatlar: # Henüz yedek yoksa
                    print(f"ℹ️ Yedek olarak {ilce_adi} tutuluyor...")
                    bulunan_fiyatlar = temp_fiyat

        # Döngü bitti, hedef ilçe bulamadıysak yedeği döndür
        if bulunan_fiyatlar:
            if bulunan_fiyatlar["LPG"] is None: bulunan_fiyatlar["LPG"] = "---"
            return bulunan_fiyatlar
        
        return None

    except Exception as e:
        print(f"❌ Hata: {e}")
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
        
        tweet = f"""⛽ GÜNCEL AKARYAKIT FİYATLARI 🇹🇷

Benzi̇n:  {fiyatlar['Benzin']} TL
Motori̇n: {fiyatlar['Motorin']} TL

📅 Tarih: {time.strftime("%d.%m.%Y")}

#akaryakıt #benzin #motorin #lpg #zam #indirim"""

        client.create_tweet(text=tweet)
        print(f"🚀 BAŞARILI! TWEET ATILDI! Profiline Bak!")
        
    except Exception as e:
        print(f"❌ Tweet atarken hata: {e}")

# ==========================================
# 4. BAŞLAT
# ==========================================
if __name__ == "__main__":
    veriler = fiyatlari_getir()
    
    if veriler:
        print(f"\n💰 TWEET ATILACAK VERİLER:\n{veriler}")
        soru = input("\nTweet gönderilsin mi? (e/h): ")
        if soru.lower() == "e":
            tweet_at(veriler)
        else:
            print("İptal edildi.")
    else:
        print("❌ Uygun veri bulunamadı.")
