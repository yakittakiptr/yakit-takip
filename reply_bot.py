import tweepy
import os
import json
import time

# ==========================================
# 1. AYARLAR (GitHub Secrets'tan okunur)
# ==========================================
# NOT: Bu kısım, şifreleri GitHub'ın güvenli kasasından okur
API_KEY = os.environ.get("TWITTER_API_KEY")
API_SECRET = os.environ.get("TWITTER_API_SECRET")
ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET")

# HEDEF HESAPLAR VE KELİMELER
HEDEF_HESAPLAR = ["ntvpara", "haberturk", "bloomberght", "ekonomist_dergi"]
ARANACAK_KELIMELER = ["zam", "indirim", "akaryakıt", "benzin", "motorin", "lpg"]
REPLIED_FILE = "replied_ids.txt"

# ==========================================
# 2. VERİ VE HATA YÖNETİMİ
# ==========================================

def get_last_prices():
    """ Kaydedilen son fiyatları JSON dosyasından okur. """
    try:
        # main.py tarafından oluşturulan dosyayı okur
        with open('last_prices.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fiyat dosyası okunamadı. Hata: {e}") 
        return None

def get_replied_ids():
    """ Daha önce cevaplanan tweet ID'lerini okur (Spam engeli). """
    if not os.path.exists(REPLIED_FILE):
        return set()
    try:
        # Önceki çalıştırmadan kalan ID'leri okur
        with open(REPLIED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except Exception as e:
        print(f"❌ Replied ID dosyası okuma hatası: {e}")
        return set()

def save_replied_id(tweet_id):
    """ Cevaplanan tweet ID'sini dosyaya kaydeder. """
    with open(REPLIED_FILE, 'a') as f:
        f.write(f"{tweet_id}\n")

# ==========================================
# 3. YANIT MOTORU
# ==========================================

def reply_to_targets(fiyatlar):
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    
    replied_ids = get_replied_ids()
    
    # 1. Güncel Fiyat Metnini Hazırla
    fiyat_metni = (
        f"⛽ Benzin: {fiyatlar['Benzin']} TL | "
        f"🚛 Motorin: {fiyatlar['Motorin']} TL | "
        f"🔥 LPG: {fiyatlar['LPG']} TL"
    )
    
    # 2. Arama Sorgusu (Sadece hedef hesaplara ve alakalı kelimelere odaklan)
    query = f"({' OR '.join(ARANACAK_KELIMELER)}) from:{' OR from:'.join(HEDEF_HESAPLAR)} -is:retweet"

    try:
        print(f"🔍 Aranan Sorgu: {query}")
        # Sonuçları alma (API limitlerini korumak için 5 sonuç ile sınırlı)
        response = client.search_recent_tweets(query=query, max_results=5) 

        if not response.data:
            print("ℹ️ Yeni hedef tweet bulunamadı.")
            return

        for tweet in response.data:
            tweet_id = str(tweet.id)
            
            # Daha önce cevaplandıysa atla
            if tweet_id in replied_ids:
                continue

            # Cevap Metnini Oluştur
            cevap_metni = (
                f"✅ GÜNCEL AKARYAKIT FİYATLARI\n"
                f"{fiyat_metni}\n"
                f"Kaynak: Opet (İst. Anadolu)"
            )
            
            # Cevabı Gönder
            client.create_tweet(text=cevap_metni, in_reply_to_tweet_id=tweet_id)
            print(f"🚀 Başarılı: Cevap atıldı! Tweet ID: {tweet_id}")
            save_replied_id(tweet_id) # Cevaplandı olarak kaydet
            time.sleep(5) # Anti-spam: Ard arda tweet atmamak için bekle
            # Sadece bir tweete cevap attıktan sonra çık, API limitini koru
            return
            
    except tweepy.errors.TooManyRequests as e:
        print(f"❌ API Limitine Ulaşıldı. Saat başı çalışmaya devam edecek.")
    except Exception as e:
        print(f"❌ Yanıt Botu Genel Hata: {e}")

# ==========================================
# 4. BAŞLAT
# ==========================================

if __name__ == "__main__":
    prices = get_last_prices()
    
    if prices:
        reply_to_targets(prices)
    else:
        print("❌ Fiyat verisi olmadığı için yanıt atlanıyor.")
