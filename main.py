import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
import requests
import json

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÜVENLİK
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CPM/RPM Calculator", layout="wide", page_icon="🧮")

# Tabloyu daha okunur yapmak için CSS
st.markdown("""
<style>
    .big-font { font-size: 18px !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (SADECE GERÇEK VERİYİ ALIR)
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    # Make.com Webhook Linkin (Temiz hali)
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def get_avg_views_from_json(row):
    """
    Supabase'deki JSON verisinden SADECE 'avg_video_views' verisini çeker.
    Bu bizim 'Number of Impressions' değerimizdir.
    """
    raw_data = row.get('posts_raw_data')
    
    # Varsayılan 0
    if not raw_data: return 0
    
    try:
        posts = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except:
        return 0

    views_list = []
    
    if isinstance(posts, list):
        for post in posts:
            # Sadece izlenme sayısı olanları (Videoları) al
            views = post.get('videoViewCount') or post.get('playCount') or 0
            if views > 0:
                views_list.append(views)

    # Eğer hiç video yoksa 0 döndür, varsa ortalamasını al
    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_pure_metrics(row, cost_of_ad, total_revenue):
    """
    SENİN İSTEDİĞİN SAF FORMÜLLER:
    1. CPM = (Cost of the Ad / Number of Impressions) x 1,000
    2. RPM = (Total revenue generated / Number of Pageviews) x 1,000
    """
    # Impressions = Ortalama Video İzlenmesi (Pageviews yerine geçer)
    impressions = row.get('avg_views', 0)
    
    # Sıfıra bölme hatasını engelle
    if impressions <= 0:
        return pd.Series([0, 0], index=['CPM ($)', 'RPM ($)'])

    # --- 1. CPM HESABI ---
    # Formül: (Cost / Impressions) * 1000
    cpm = (cost_of_ad / impressions) * 1000
    
    # --- 2. RPM HESABI ---
    # Formül: (Revenue / Impressions) * 1000
    rpm = (total_revenue / impressions) * 1000
    
    return pd.Series([cpm, rpm], index=['CPM ($)', 'RPM ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (FRONTEND)
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center;'>🔒 Finansal Analiz Girişi</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Giriş Başarısız")

# --- DASHBOARD ---
else:
    # --- YAN MENÜ (KULLANICI GİRDİLERİ) ---
    with st.sidebar:
        st.title("💰 Bütçe Simülasyonu")
        st.info("Formüller için kullanılacak değerleri girin:")
        
        # 1. Cost of the Ad (Kullanıcı Belirler)
        cost_of_ad = st.number_input("Cost of the Ad ($)", value=1000, step=100, help="Bu reklama harcamayı planladığınız toplam bütçe.")
        
        # 2. Total Revenue Generated (Kullanıcı Belirler)
        total_revenue = st.number_input("Total Revenue Generated ($)", value=1500, step=100, help="Bu reklamdan elde etmeyi beklediğiniz toplam ciro.")
        
        st.markdown("---")
        st.subheader("Yeni Analiz")
        new_u = st.text_input("Kullanıcı Adı:")
        if st.button("Analiz Et 🚀"):
            if new_u:
                trigger_webhook(new_u)
                st.success("Veri çekiliyor...")
        
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ANA EKRAN ---
    st.title("📊 Saf CPM & RPM Hesaplayıcı")
    st.markdown(f"""
    Bu tablo, **${cost_of_ad:,}** reklam bütçesi harcadığınızda ve **${total_revenue:,}** gelir elde ettiğinizde, 
    influencer'ların izlenme sayılarına göre oluşacak birim maliyetleri gösterir.
    """)
    
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 1. Gerçek İzlenme Sayısını (Impressions) Çek
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        
        # 2. SADECE CPM ve RPM Hesapla (Senin Formüllerinle)
        financials = df.apply(calculate_pure_metrics, args=(cost_of_ad, total_revenue), axis=1)
        df = pd.concat([df, financials], axis=1)
        
        # 3. Görselleştirme
        
        # Sadece videosu olanları göster
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            # TABLO
            st.subheader("📋 Karşılaştırma Tablosu")
            
            # Tabloyu, CPM'i en düşük (en ucuz) olandan yükseğe doğru sıralayalım
            df_valid = df_valid.sort_values(by="CPM ($)", ascending=True)
            
            st.dataframe(
                df_valid[['username', 'avg_views', 'CPM ($)', 'RPM ($)']].style.format({
                    "avg_views": "{:,.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}"
                }),
                use_container_width=True,
                height=400
            )
            
            # KAZANANIN ANALİZİ
            best_cpm = df_valid.iloc[0]
            st.success(f"""
            🏆 **Maliyet Şampiyonu:** **{best_cpm['username']}**
            - Eğer **${cost_of_ad}** bütçeyi bu kişiye verirseniz, her 1000 kişi için sadece **${best_cpm['CPM ($)']:.2f}** ödersiniz.
            - Bu, listedeki en verimli reklam maliyetidir.
            """)
            
            # GRAFİK
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📉 CPM Karşılaştırması (Düşük İyidir)")
                fig_cpm = px.bar(
                    df_valid, 
                    x='username', 
                    y='CPM ($)', 
                    color='CPM ($)',
                    title=f"${cost_of_ad} Bütçe için CPM Maliyetleri",
                    text_auto='.2f',
                    color_continuous_scale='Reds' # Kırmızı pahalı demek
                )
                st.plotly_chart(fig_cpm, use_container_width=True)
                
            with col2:
                st.subheader("📈 RPM Karşılaştırması (Yüksek İyidir)")
                fig_rpm = px.bar(
                    df_valid, 
                    x='username', 
                    y='RPM ($)', 
                    color='RPM ($)',
                    title=f"${total_revenue} Gelir için RPM Değerleri",
                    text_auto='.2f',
                    color_continuous_scale='Greens' # Yeşil kazanç demek
                )
                st.plotly_chart(fig_rpm, use_container_width=True)
            
        else:
            st.warning("Henüz video verisi olan bir influencer yok. Lütfen yeni analiz ekleyin.")

    else:
        st.info("Veritabanı boş.")
