import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import requests
import json
import time  # Sayfa yenileme gecikmesi için eklendi

# -----------------------------------------------------------------------------
# 1. AYARLAR VE TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer ROI Simülatörü", layout="wide", page_icon="💸")

# Özel CSS: Kartlar ve Tablo Düzeni
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #d6d6d6;
    }
    div[data-testid="stMetricValue"] { font-size: 20px; color: #333; }
    .profit { color: green; font-weight: bold; }
    .loss { color: red; font-weight: bold; }
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
# 2. FONKSİYONLAR (Veri İşleme)
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x" 
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

# --- YENİ EKLENEN FONKSİYON: VERİTABANI TEMİZLEME ---
def clear_database():
    """Supabase tablosundaki tüm verileri siler"""
    try:
        # 'id' sütunu 0'a eşit olmayan (yani hepsi) verileri sil
        supabase.table('influencers').delete().neq("id", 0).execute()
        return True
    except Exception as e:
        st.error(f"Silme işlemi başarısız: {e}")
        return False
# ----------------------------------------------------

def safe_json_parse(raw_data):
    """JSON Format Düzeltici"""
    if not raw_data: return []
    if isinstance(raw_data, list): return raw_data
    if not isinstance(raw_data, str): return []
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        try:
            return json.loads(f"[{raw_data}]")
        except:
            return []

def get_avg_views_from_json(row):
    """Ortalama İzlenme Hesaplayıcı"""
    raw_data = row.get('posts_raw_data')
    posts = safe_json_parse(raw_data)
    views_list = []
    
    if posts and isinstance(posts, list):
        for post in posts:
            views = post.get('videoViewCount') or post.get('playCount') or post.get('viewCount') or 0
            if views > 0: views_list.append(views)

    if views_list:
        return int(sum(views_list) / len(views_list))
    else:
        return 0

def calculate_roi_metrics(row, ad_cost, clicks, product_price):
    """
    YENİ FORMÜLLER:
    CPM = (Reklam Maliyeti / İzlenme) * 1000
    RPM = ((Tıklanma * Ürün Fiyatı) / İzlenme) * 1000
    Kâr/Zarar = RPM - CPM
    """
    views = row.get('avg_views', 0)
    
    if views <= 0:
        return pd.Series([0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

    # 1. CPM (Maliyet)
    cpm = (ad_cost / views) * 1000
    
    # 2. RPM (Gelir Potansiyeli)
    total_revenue = clicks * product_price # Toplam Beklenen Ciro
    rpm = (total_revenue / views) * 1000
    
    # 3. Fark (Profitability)
    diff = rpm - cpm
    
    return pd.Series([cpm, rpm, diff], index=['CPM ($)', 'RPM ($)', 'Fark ($)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (UI)
# -----------------------------------------------------------------------------

# --- GİRİŞ EKRANI ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align: center;'>🔐 Giriş</h2>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            if st.form_submit_button("Panel'e Git", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state['logged_in'] = True
                    st.rerun()
                except:
                    st.error("Hatalı Giriş")

# --- ANA DASHBOARD ---
else:
    # Sidebar (Sadece İşlemler)
    with st.sidebar:
        st.header("⚙️ İşlemler")
        new_u = st.text_input("Yeni Kişi Ekle:")
        if st.button("Analiz Başlat 🚀"):
            if new_u:
                trigger_webhook(new_u)
                st.success("İstek gönderildi.")
        
        st.divider()
        
        # --- YENİ EKLENEN BUTON: VERİLERİ TEMİZLE ---
        st.markdown("### ⚠️ Veri Yönetimi")
        if st.button("🗑️ Tüm Listeyi Temizle", type="primary", use_container_width=True):
            with st.spinner("Veritabanı temizleniyor..."):
                if clear_database():
                    st.success("Tüm veriler silindi!")
                    time.sleep(1) # Kullanıcı mesajı görsün diye bekle
                    st.rerun()    # Sayfayı yenile
        # --------------------------------------------

        st.divider()
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ÜST PANEL: SİMÜLASYON GİRDİLERİ (INPUTS) ---
    st.title("📈 Influencer Kârlılık Simülatörü")
    st.markdown("Aşağıdaki parametreleri değiştirerek **CPM (Maliyet)** ve **RPM (Gelir)** senaryolarını test edin.")

    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("### 1. Reklam Maliyeti")
            ad_cost = st.number_input("Influencer'a Ödenecek Tutar ($)", value=1000, step=100, help="Cost of the Ad")
            
        with c2:
            st.markdown("### 2. Beklenen Etkileşim")
            exp_clicks = st.number_input("Tahmini Tıklanma Sayısı", value=500, step=50, help="Influencer'dan kaç kişi linke tıklar?")
            
        with c3:
            st.markdown("### 3. Ürün Değeri")
            prod_price = st.number_input("Ürün Satış Fiyatı ($)", value=30.0, step=5.0, help="Sattığınız ürünün ortalama fiyatı")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Hızlı Hesap Göstergesi
        total_potential_revenue = exp_clicks * prod_price
        roi_status = "KÂR" if total_potential_revenue > ad_cost else "ZARAR"
        roi_color = "green" if total_potential_revenue > ad_cost else "red"
        
        st.markdown(f"""
        <p style='text-align: center; font-size: 18px;'>
        Bu senaryoda toplam <b>${total_potential_revenue:,.0f}</b> ciro hedefleniyor. 
        Maliyet çıktıktan sonra durum: <span style='color:{roi_color}; font-weight:bold'>{roi_status} (${total_potential_revenue - ad_cost:,.0f})</span>
        </p>
        """, unsafe_allow_html=True)

    # --- VERİ ÇEKME VE HESAPLAMA ---
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # --- Hata Düzeltici (Niche Kontrolü) ---
        if 'Niche' not in df.columns:
            if 'niche' in df.columns:
                df['Niche'] = df['niche']
            else:
                df['Niche'] = "-"
        # ---------------------------------------

        # 1. Ort. İzlenme Hesabı
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)
        
        # 2. CPM / RPM / Fark Hesabı (Yeni Formüllerle)
        metrics = df.apply(calculate_roi_metrics, args=(ad_cost, exp_clicks, prod_price), axis=1)
        df = pd.concat([df, metrics], axis=1)
        
        # Sadece verisi olanları al
        df_valid = df[df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            # 3. EN KÂRLI OLANI BUL (Grafik İçin)
            # Fark ($) sütununa göre sırala (En yüksek kâr en üstte)
            df_valid = df_valid.sort_values(by="Fark ($)", ascending=False)
            
            # --- TABLO ---
            st.subheader("📋 Detaylı Analiz Tablosu")
            
            # Gösterilecek Sütunlar
            table_cols = ['username', 'Niche', 'avg_views', 'CPM ($)', 'RPM ($)', 'Fark ($)']
            
            # Tabloyu Renklendirme Fonksiyonu
            def highlight_profit(val):
                color = '#d4edda' if val > 0 else '#f8d7da' # Yeşil veya Kırmızı arka plan
                return f'background-color: {color}'

            st.dataframe(
                df_valid[table_cols].style.format({
                    "avg_views": "{:,.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}",
                    "Fark ($)": "${:+.2f}" # Artı/Eksi işareti koy
                }).applymap(highlight_profit, subset=['Fark ($)']),
                use_container_width=True,
                height=400
            )
            
            # --- GRAFİK ---
            st.markdown("---")
            st.subheader("🏆 Kârlılık Karşılaştırması (RPM - CPM)")
            st.caption("Çubuk ne kadar yüksekse, Influencer o kadar kârlıdır. Sıfırın altı zarar demektir.")
            
            fig = px.bar(
                df_valid,
                x='username',
                y='Fark ($)',
                color='Fark ($)',
                text_auto='+.2f',
                title="Hangi Influencer Daha Fazla Kazandırır?",
                color_continuous_scale=['red', 'green'], # Kırmızıdan Yeşile
                labels={'Fark ($)': 'Net Kâr Potansiyeli (Birim Başına)'}
            )
            # Sıfır çizgisini ekle
            fig.add_hline(y=0, line_dash="dot", annotation_text="Başabaş Noktası", annotation_position="bottom right")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Veri var ama videolu gönderi bulunamadı.")
    else:
        st.info("Veritabanı boş.")
