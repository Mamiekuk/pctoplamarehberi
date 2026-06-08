import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

STRAPI_API_URL = os.getenv("STRAPI_API_URL", "http://localhost:1337")

# Sayfa Ayarları
st.set_page_config(
    page_title="PC Build Guide / PC Toplama Rehberi",
    page_icon="💻",
    layout="wide"
)

# Custom CSS - Modern Arayüz (Dark Mode uyumlu)
st.markdown("""
<style>
    /* Ana arkaplan ve metin ayarları */
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Kart yapısı */
    .system-card {
        background: rgba(30, 30, 30, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        transition: transform 0.2s, box-shadow 0.2s;
        backdrop-filter: blur(10px);
    }
    .system-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Başlıklar */
    h1, h2, h3, h4 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Fiyat etiketi */
    .price-tag {
        font-size: 1.5em;
        font-weight: bold;
        color: #00e676; /* Neon yeşil */
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    /* Donanım bilgisi metni */
    .hardware-info {
        color: #b0bec5;
        font-size: 0.95em;
        margin-bottom: 15px;
        padding-left: 10px;
        border-left: 3px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# Dil Seçimi (Sidebar)
selected_language = st.sidebar.radio("Language / Dil", options=["Türkçe (TR)", "English (EN)"])
locale = "tr" if "TR" in selected_language else "en"

# Çeviri Metinleri
texts = {
    "tr": {
        "title": "⚡ Yeni Nesil PC Toplama Rehberi",
        "subtitle": "Kullanım amacınıza en uygun, yapay zeka destekli bilgisayar sistemlerini keşfedin.",
        "category_select": "Kategori Seçin",
        "price_label": "Fiyat: ",
        "hardware_label": "Donanım Özellikleri",
        "details_label": "Sistem Detayları",
        "currency": "₺",
        "error_fetch": "Veriler çekilirken bir hata oluştu. Strapi sunucusunun çalıştığından emin olun."
    },
    "en": {
        "title": "⚡ Next-Gen PC Building Guide",
        "subtitle": "Discover AI-powered computer systems best suited for your needs.",
        "category_select": "Select Category",
        "price_label": "Price: ",
        "hardware_label": "Hardware Specs",
        "details_label": "System Details",
        "currency": "₺", 
        "error_fetch": "Error fetching data. Please ensure Strapi server is running."
    }
}
t = texts[locale]

st.title(t["title"])
st.markdown(f"*{t['subtitle']}*")
st.markdown("---")

# Strapi'den Veri Çekme Fonksiyonları
@st.cache_data(ttl=60) # 1 dakika cache'le
def get_categories(loc):
    try:
        res = requests.get(f"{STRAPI_API_URL}/api/categories?locale={loc}")
        if res.status_code == 200:
            return res.json().get("data", [])
        return []
    except:
        return []

@st.cache_data(ttl=60)
def get_systems(loc):
    try:
        res = requests.get(f"{STRAPI_API_URL}/api/systems?populate=*&locale={loc}")
        if res.status_code == 200:
            return res.json().get("data", [])
        return []
    except:
        return []

categories = get_categories(locale)
systems = get_systems(locale)

if not categories and not systems:
    st.error(t["error_fetch"])
else:
    st.sidebar.header(t["category_select"])
    
    cat_options = ["Tümü" if locale == "tr" else "All"]
    for cat in categories:
        attrs = cat.get("attributes", cat)
        if "name" in attrs:
            cat_options.append(attrs["name"])
            
    selected_cat = st.sidebar.selectbox("", cat_options)

    filtered_systems = []
    if selected_cat in ["Tümü", "All"]:
        filtered_systems = systems
    else:
        for sys in systems:
            sys_attrs = sys.get("attributes", sys)
            sys_cat = sys_attrs.get("category", {})
            
            if sys_cat:
                 sys_cat_data = sys_cat.get("data", {})
                 if sys_cat_data:
                     sys_cat_attrs = sys_cat_data.get("attributes", sys_cat_data)
                     if sys_cat_attrs.get("name") == selected_cat:
                         filtered_systems.append(sys)
                 elif sys_cat.get("name") == selected_cat:
                     filtered_systems.append(sys)

    if not filtered_systems:
        st.info("Bu kategoride henüz bir sistem bulunmuyor." if locale == "tr" else "No systems found in this category yet.")
    
    for sys in filtered_systems:
        attrs = sys.get("attributes", sys)
        name = attrs.get("name", "Bilinmeyen Sistem")
        hardware = attrs.get("hardware_info", "")
        details = attrs.get("details", "")
        price = attrs.get("price", 0)
        
        image_url = None
        img_data = attrs.get("image", {})
        
        if img_data:
            img_obj = img_data.get("data")
            if img_obj:
                img_attrs = img_obj.get("attributes", img_obj)
                image_url = STRAPI_API_URL + img_attrs.get("url", "")
            elif img_data.get("url"):
                image_url = STRAPI_API_URL + img_data.get("url")

        with st.container():
            st.markdown(f'<div class="system-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if image_url:
                    st.image(image_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/400x300.png?text=No+Image", use_container_width=True)
            
            with col2:
                st.subheader(name)
                st.markdown(f'<div class="price-tag">{price:,.2f} {t["currency"]}</div>', unsafe_allow_html=True)
                
                st.markdown(f"**{t['hardware_label']}:**")
                st.markdown(f'<div class="hardware-info">{hardware}</div>', unsafe_allow_html=True)
                
                with st.expander(t["details_label"]):
                    st.write(details)
                    
            st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.info("🚀 Powered by Streamlit & Strapi & Pollinations AI")
