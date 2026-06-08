import os
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import time
import urllib.request
import urllib.parse

# .env dosyasını yükle
load_dotenv()

STRAPI_API_URL = os.getenv("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.getenv("STRAPI_API_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
}

MOCK_CATEGORIES = [
    {"name": "Oyun Bilgisayarı", "description": "Yüksek performanslı oyun sistemleri."},
    {"name": "Ofis Bilgisayarı", "description": "Günlük işler ve ofis kullanımı için uygun fiyatlı sistemler."},
    {"name": "Yazılım/Render Sistemi", "description": "Ağır iş yükleri, render ve yazılım geliştirme için güçlü sistemler."}
]

MOCK_SYSTEMS = [
    {
        "name": "Titan X Gaming PC",
        "hardware_info": "AMD Ryzen 7 7800X3D, RTX 4080 Super, 32GB DDR5 RAM",
        "details": "En güncel oyunları 4K çözünürlükte ultra ayarlarda oynamak için tasarlanmış üst düzey sistem.",
        "price": 85000,
        "category_name": "Oyun Bilgisayarı",
        "image_prompt": "High-end neon lit gaming pc setup, dark room, cyberpunk style, hyper-realistic"
    },
    {
        "name": "Office Pro Desktop",
        "hardware_info": "Intel Core i5-13400, Intel UHD Graphics, 16GB DDR4 RAM",
        "details": "Ofis programları, muhasebe yazılımları ve internet kullanımı için sessiz ve verimli sistem.",
        "price": 18500,
        "category_name": "Ofis Bilgisayarı",
        "image_prompt": "Clean minimal office desk with a modern desktop computer, bright lighting, professional, realistic"
    },
    {
        "name": "Render Beast Studio",
        "hardware_info": "Intel Core i9-14900K, RTX 4090, 64GB DDR5 RAM",
        "details": "3D modelleme, video kurgu ve yapay zeka eğitimleri için sınırları zorlayan render sistemi.",
        "price": 145000,
        "category_name": "Yazılım/Render Sistemi",
        "image_prompt": "Professional workstation computer with multiple monitors showing code and 3D models, creative studio environment"
    }
]

translator = GoogleTranslator(source='tr', target='en')

def upload_image_to_strapi(image_path):
    print(f"📷 {image_path} Strapi'ye yükleniyor...")
    upload_url = f"{STRAPI_API_URL}/api/upload"
    
    try:
        with open(image_path, "rb") as f:
            files = {"files": f}
            response = requests.post(upload_url, headers=HEADERS, files=files)
            
            if response.status_code == 200:
                data = response.json()
                return data[0]["id"]
            else:
                print(f"❌ Görsel yükleme hatası: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Beklenmeyen hata (Görsel Yükleme): {e}")
        return None

def generate_image(prompt, filename):
    print(f"🎨 YZ görsel üretiliyor: {filename}")
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=600&nologo=true"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            print("❌ Görsel indirilemedi.")
            return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata (Görsel Üretimi): {e}")
        return False

def get_categories():
    print("🔍 Kategoriler kontrol ediliyor...")
    try:
        response = requests.get(f"{STRAPI_API_URL}/api/categories?locale=all", headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception as e:
        print(f"Hata: {e}")
        return []

def create_category(category_data):
    print(f"📁 Kategori oluşturuluyor: {category_data['name']}")
    try:
        # TR olarak kaydet
        payload = {
            "data": {
                "name": category_data["name"],
                "description": category_data["description"]
            }
        }
        res = requests.post(f"{STRAPI_API_URL}/api/categories", headers=HEADERS, json=payload)
        
        if res.status_code in [200, 201]:
            data = res.json()
            
            # Strapi v5 (documentId) vs Strapi v4 (id) kontrolü
            tr_document_id = data.get("data", {}).get("documentId")
            tr_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) and "id" in data.get("data") else data.get("id")
            
            identifier = tr_document_id if tr_document_id else tr_id
            
            if identifier:
                # EN Çeviri ve Localization
                en_name = translator.translate(category_data["name"])
                en_desc = translator.translate(category_data["description"])
                
                # Strapi v5'te localization verisi "data" objesi içine sarılmalıdır
                if tr_document_id:
                    loc_payload = {
                        "data": {
                            "name": en_name,
                            "description": en_desc,
                            "locale": "en"
                        }
                    }
                else:
                    loc_payload = {
                        "name": en_name,
                        "description": en_desc,
                        "locale": "en"
                    }
                
                loc_res = requests.post(f"{STRAPI_API_URL}/api/categories/{identifier}/localizations", headers=HEADERS, json=loc_payload)
                if loc_res.status_code in [200, 201]:
                    print(f"✅ Kategori çok dilli (tek post) olarak eklendi: {category_data['name']}")
                else:
                    print(f"⚠️ Kategori TR eklendi ama EN çevirisi eklenemedi: {loc_res.text}")
                
                return identifier
        else:
            print(f"❌ Kategori eklenirken hata: {res.text}")
            return None
    except Exception as e:
        print(f"❌ Beklenmeyen Hata: {e}")
        return None

def create_system(system_data, category_id):
    print(f"💻 Sistem oluşturuluyor: {system_data['name']}")
    try:
        # Önce görseli üret ve indir
        image_filename = f"{system_data['name'].replace(' ', '_').lower()}.jpg"
        if generate_image(system_data['image_prompt'], image_filename):
            # Strapi'ye yükle
            image_id = upload_image_to_strapi(image_filename)
        else:
            image_id = None
        
        # Sistemi TR olarak ekle
        payload = {
            "data": {
                "name": system_data["name"],
                "hardware_info": system_data["hardware_info"],
                "details": system_data["details"],
                "price": system_data["price"],
                "category": category_id,
                "image": image_id
            }
        }
        
        res = requests.post(f"{STRAPI_API_URL}/api/systems", headers=HEADERS, json=payload)
        
        if res.status_code in [200, 201]:
            data = res.json()
            
            tr_document_id = data.get("data", {}).get("documentId")
            tr_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) and "id" in data.get("data") else data.get("id")
            
            identifier = tr_document_id if tr_document_id else tr_id
            
            if identifier:
                # İngilizceye Çevir
                en_name = system_data["name"]
                en_hardware = system_data["hardware_info"]
                en_details = translator.translate(system_data["details"])
                
                if tr_document_id:
                    loc_payload = {
                        "data": {
                            "name": en_name,
                            "hardware_info": en_hardware,
                            "details": en_details,
                            "price": system_data["price"],
                            "category": category_id,
                            "image": image_id,
                            "locale": "en"
                        }
                    }
                else:
                    loc_payload = {
                        "name": en_name,
                        "hardware_info": en_hardware,
                        "details": en_details,
                        "price": system_data["price"],
                        "category": category_id,
                        "image": image_id,
                        "locale": "en"
                    }
                
                loc_res = requests.post(f"{STRAPI_API_URL}/api/systems/{identifier}/localizations", headers=HEADERS, json=loc_payload)
                if loc_res.status_code in [200, 201]:
                    print(f"✅ Sistem çok dilli (tek post) olarak eklendi: {system_data['name']}")
                else:
                    print(f"⚠️ Sistem TR eklendi ama EN çevirisi eklenemedi: {loc_res.text}")
        else:
            print(f"❌ Sistem eklenirken hata: {res.text}")
            
    except Exception as e:
         print(f"❌ Beklenmeyen Hata: {e}")

def run():
    print("🚀 Otomasyon Başlatılıyor...")
    if not STRAPI_API_TOKEN:
        print("❌ HATA: .env dosyasında STRAPI_API_TOKEN bulunamadı!")
        return

    # Önce kategorileri kontrol et ve oluştur
    existing_categories = get_categories()
    category_map = {}
    
    for cat in existing_categories:
        attrs = cat.get("attributes", cat)
        name = attrs.get("name") if attrs else cat.get("name")
        if name:
            # Strapi v5 documentId vs Strapi v4 id
            category_map[name] = cat.get("documentId", cat.get("id"))

    for mock_cat in MOCK_CATEGORIES:
        if mock_cat["name"] not in category_map:
            cat_id = create_category(mock_cat)
            if cat_id:
                category_map[mock_cat["name"]] = cat_id

    # Sistemleri oluştur
    for mock_sys in MOCK_SYSTEMS:
        cat_id = category_map.get(mock_sys["category_name"])
        if cat_id:
            create_system(mock_sys, cat_id)
            time.sleep(2) # İşlemler arası kısa bekleme
        else:
            print(f"❌ Sistem için Kategori bulunamadı: {mock_sys['category_name']}")
            
    print("🎉 Otomasyon Tamamlandı!")

if __name__ == "__main__":
    run()
