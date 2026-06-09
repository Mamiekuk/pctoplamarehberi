import os
import requests
import json
from dotenv import load_dotenv
import time
import random
import urllib.request
import urllib.parse
from groq import Groq

# .env dosyasını yükle
load_dotenv()

STRAPI_API_URL = os.getenv("STRAPI_API_URL", "http://localhost:1337").rstrip("/")
STRAPI_API_TOKEN = os.getenv("STRAPI_API_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
}

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    print("⚠️ UYARI: GROQ_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")
    groq_client = None

MOCK_CATEGORIES = [
    {"name": "Oyun Bilgisayarı", "description": "Yüksek performanslı oyun sistemleri."},
    {"name": "Ofis Bilgisayarı", "description": "Günlük işler ve ofis kullanımı için uygun fiyatlı sistemler."},
    {"name": "Yazılım/Render Sistemi", "description": "Ağır iş yükleri, render ve yazılım geliştirme için güçlü sistemler."}
]

def groq_translate(text):
    if not groq_client:
        return text
    print(f"🌍 Groq Çeviri: {text[:20]}...")
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given Turkish text to English. Return ONLY the English translation without any extra text, quotes, or explanations."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=256,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Groq çeviri hatası: {e}")
        return text

def groq_enhance_prompt(name, hardware_info, category):
    if not groq_client:
        return f"A high quality studio shot of a {category} computer named {name}, highly detailed."
    print(f"🧠 Groq görsel komutu üretiyor: {name}")
    try:
        prompt_instruction = f"""
        Write a highly detailed, professional text-to-image prompt for a computer system.
        Name: {name}
        Category: {category}
        Specs: {hardware_info}
        
        The image should be a hyper-realistic, 8k resolution, cinematic studio shot of the PC desktop case and setup. 
        It must reflect its category (e.g., RGB lights for gaming, clean desk for office, creative studio for render).
        Return ONLY the English image prompt, nothing else. No quotes, no intro.
        """
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_instruction}],
            temperature=0.7,
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"A high quality studio shot of a {category} computer named {name}, highly detailed."

def get_existing_names():
    url = f"{STRAPI_API_URL}/api/systems?fields=name&locale=tr-TR&pagination[pageSize]=100"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            data = res.json().get("data", [])
            return [sys.get("name") for sys in data if sys.get("name")]
    except:
        pass
    return []

def groq_generate_systems(category_name, count):
    if not groq_client:
        return []
    print(f"🤖 Groq '{category_name}' için {count} adet güncel bilgisayar sistemi tasarlıyor...")
    
    themes = ["Uzay ve Galaksi", "Mitolojik Tanrılar", "Siberpunk & Neon", "Yırtıcı Hayvanlar", "Askeri ve Taktiksel", "Otomobil Yarışları", "Samuray ve Ninja", "Doğa ve Elementler", "Karanlık ve Gotik", "Minimalist ve Modern"]
    selected_theme = random.choice(themes)
    
    existing_names = get_existing_names()
    avoid_names_str = f"CRITICAL: Do NOT use any of these existing names: {', '.join(existing_names)}." if existing_names else "Ensure each name is completely unique and never used before."
    
    try:
        prompt_instruction = f"""
        You are an expert PC builder. Generate {count} realistic, modern PC builds for the category: "{category_name}".
        CRITICAL: The naming and aesthetic concept of these PCs MUST be inspired by the theme: '{selected_theme}'.
        {avoid_names_str}
        Provide the output ONLY as a valid JSON array of objects.
        Each object MUST have the following keys:
        - name: A cool, highly creative, and unique name for the PC based on the theme '{selected_theme}' (in Turkish, e.g. 'Galaktik Fırtına', 'Neon Samuray'). DO NOT use boring generic names like 'Oyun Canavarı' or 'Ofis Pro'.
        - hardware_info: Detailed specs (CPU, GPU, RAM, Motherboard, Storage). Ensure the hardware matches the tier of the PC.
        - details: Write an engaging 2-3 sentence AI commentary evaluating this system's performance, its target audience, and why it is a great choice. Tie the commentary slightly into the '{selected_theme}' theme (in Turkish). NEVER leave this empty or write 'none'.
        - price: Realistic price in Turkish Lira (TRY) as an integer number (e.g. 25000).
        
        Example JSON structure:
        [
            {{"name": "...", "hardware_info": "...", "details": "...", "price": 25000}}
        ]
        Respond with ONLY the raw JSON array. Do not include markdown code blocks.
        """
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_instruction}],
            temperature=0.7,
            max_tokens=1024,
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Temizlik (Eğer yapay zeka markdown gönderirse temizle)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        systems = json.loads(response_text.strip())
        return systems
    except Exception as e:
        print(f"❌ Groq sistem üretme hatası: {e}")
        return []

def upload_image_to_strapi(image_path):
    print(f"📷 {image_path} Strapi'ye yükleniyor...")
    upload_url = f"{STRAPI_API_URL}/api/upload"
    try:
        with open(image_path, "rb") as f:
            files = {"files": (image_path, f, "image/jpeg")}
            response = requests.post(upload_url, headers=HEADERS, files=files)
            if response.status_code in [200, 201]:
                data = response.json()
                return data[0]["id"]
            else:
                return None
    except Exception as e:
        return None

def generate_image(prompt, filename):
    print(f"🎨 YZ görsel üretiliyor (Hugging Face): {filename}")
    API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY", "")
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"❌ Görsel üretilemedi ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Görsel hatası: {e}")
        return False

def get_categories():
    print("🔍 Kategoriler kontrol ediliyor...")
    try:
        response = requests.get(f"{STRAPI_API_URL}/api/categories?locale=tr-TR", headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception as e:
        return []

def create_category(category_data):
    print(f"📁 Kategori oluşturuluyor: {category_data['name']}")
    try:
        payload = {
            "data": {
                "name": category_data["name"],
                "description": category_data["description"]
            }
        }
        res = requests.post(f"{STRAPI_API_URL}/api/categories?locale=tr-TR", headers=HEADERS, json=payload)
        
        if res.status_code in [200, 201]:
            data = res.json()
            tr_document_id = data.get("data", {}).get("documentId")
            tr_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) and "id" in data.get("data") else data.get("id")
            identifier = tr_document_id if tr_document_id else tr_id
            
            if identifier:
                en_name = groq_translate(category_data["name"])
                en_desc = groq_translate(category_data["description"])
                
                if tr_document_id:
                    loc_payload = {"data": {"name": en_name, "description": en_desc}}
                    loc_res = requests.put(f"{STRAPI_API_URL}/api/categories/{tr_document_id}?locale=en", headers=HEADERS, json=loc_payload)
                else:
                    loc_payload = {"name": en_name, "description": en_desc, "locale": "en"}
                    loc_res = requests.post(f"{STRAPI_API_URL}/api/categories/{tr_id}/localizations", headers=HEADERS, json=loc_payload)
                
                if loc_res.status_code in [200, 201]:
                    print(f"✅ Kategori çok dilli olarak eklendi: {category_data['name']}")
                else:
                    print(f"⚠️ Kategori TR eklendi ama EN çevirisi eklenemedi.")
                return identifier
        else:
            print(f"❌ Kategori eklenirken hata: {res.text}")
            return None
    except Exception as e:
        print(f"❌ Beklenmeyen Hata: {e}")
        return None

def create_system(system_data, category_id, category_name):
    print(f"💻 Sistem Strapi'ye ekleniyor: {system_data['name']}")
    try:
        image_prompt = groq_enhance_prompt(system_data['name'], system_data['hardware_info'], category_name)
        image_filename = f"{system_data['name'].replace(' ', '_').lower()}.jpg"
        
        if generate_image(image_prompt, image_filename):
            image_id = upload_image_to_strapi(image_filename)
        else:
            image_id = None
        
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
        
        res = requests.post(f"{STRAPI_API_URL}/api/systems?locale=tr-TR", headers=HEADERS, json=payload)
        
        if res.status_code in [200, 201]:
            data = res.json()
            tr_document_id = data.get("data", {}).get("documentId")
            tr_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) and "id" in data.get("data") else data.get("id")
            identifier = tr_document_id if tr_document_id else tr_id
            
            if identifier:
                en_name = groq_translate(system_data["name"])
                en_hardware = system_data["hardware_info"]
                en_details = groq_translate(system_data["details"])
                
                if tr_document_id:
                    loc_payload = {"data": {"name": en_name, "hardware_info": en_hardware, "details": en_details, "price": system_data["price"], "category": category_id, "image": image_id}}
                    loc_res = requests.put(f"{STRAPI_API_URL}/api/systems/{tr_document_id}?locale=en", headers=HEADERS, json=loc_payload)
                else:
                    loc_payload = {"name": en_name, "hardware_info": en_hardware, "details": en_details, "price": system_data["price"], "category": category_id, "image": image_id, "locale": "en"}
                    loc_res = requests.post(f"{STRAPI_API_URL}/api/systems/{tr_id}/localizations", headers=HEADERS, json=loc_payload)
                    
                if loc_res.status_code in [200, 201]:
                    print(f"✅ Sistem çok dilli olarak eklendi: {system_data['name']}")
                else:
                    print(f"⚠️ Sistem TR eklendi ama EN çevirisi eklenemedi.")
        else:
            print(f"❌ Sistem eklenirken hata: {res.text}")
    except Exception as e:
         print(f"❌ Beklenmeyen Hata: {e}")

def run():
    print("🚀 Otomasyon Başlatılıyor...")
    
    # Kullanıcıdan sayı al
    try:
        count_input = input("\n👉 Her kategori için kaç adet yapay zeka destekli bilgisayar sistemi üretilsin? (Örn: 2): ")
        count = int(count_input.strip())
        if count <= 0:
            count = 2
    except ValueError:
        print("Geçersiz giriş yapıldı, varsayılan olarak 2 sistem üretilecek.")
        count = 2
        
    print(f"\n✅ Harika! Her kategori için {count} farklı bilgisayar Groq tarafından tasarlanacak...\n")

    existing_categories = get_categories()
    category_map = {}
    
    for cat in existing_categories:
        attrs = cat.get("attributes", cat)
        name = attrs.get("name") if attrs else cat.get("name")
        if name:
            category_map[name] = cat.get("documentId", cat.get("id"))

    # Kategorileri Kontrol Et ve Oluştur
    for mock_cat in MOCK_CATEGORIES:
        if mock_cat["name"] not in category_map:
            cat_id = create_category(mock_cat)
            if cat_id:
                category_map[mock_cat["name"]] = cat_id

    # Sistemleri Yapay Zekaya Ürettir ve Strapi'ye Yükle
    for mock_cat in MOCK_CATEGORIES:
        cat_name = mock_cat["name"]
        cat_id = category_map.get(cat_name)
        
        if cat_id:
            ai_systems = groq_generate_systems(cat_name, count)
            if not ai_systems:
                print(f"⚠️ {cat_name} için sistem üretilemedi, atlanıyor...")
                continue
                
            for system_data in ai_systems:
                create_system(system_data, cat_id, cat_name)
                time.sleep(2)
        else:
            print(f"❌ Sistem için Kategori bulunamadı: {cat_name}")
            
    print("\n🎉 Tüm Dinamik Yapay Zeka Sistemleri Başarıyla Eklendi!")

if __name__ == "__main__":
    run()
