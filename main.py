import streamlit as st
from supabase import create_client
import pandas as pd
import requests
import json
import time

# -----------------------------------------------------------------------------
# 1. AYARLAR VE GÖRSEL TASARIM (AYNI KALDI 🎨)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Influencer ROI Analizi", layout="wide", page_icon="🟣")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

    /* ARKA PLAN */
    .stApp {
        background: linear-gradient(120deg, #180529 0%, #3a0ca3 25%, #f72585 60%, #ff9e00 100%);
        background-attachment: fixed;
        background-size: 200% 200%;
        animation: gradientBG 15s ease infinite;
        color: white;
        font-family: 'Roboto', sans-serif;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #120524;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    section[data-testid="stSidebar"] h1, label, .stMarkdown {
        color: #e0e0e0 !important;
        font-family: 'Oswald', sans-serif;
        letter-spacing: 1px;
    }

    /* INPUT ALANLARI */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: none !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 4px !important;
        color: white !important;
    }
    input { color: white !important; }

    /* CAM KARTLAR */
    .glass-card {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: linear-gradient(to bottom, #f72585, #ff9e00);
    }

    /* BAŞLIKLAR */
    h1.hero-title {
        font-family: 'Oswald', sans-serif;
        font-size: 5rem;
        font-weight: 700;
        line-height: 1.1;
        text-transform: uppercase;
        background: -webkit-linear-gradient(top, #ffffff, #a0a0a0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    h3.subtitle {
        font-family: 'Roboto', sans-serif;
        font-weight: 300;
        font-size: 1.5rem;
        color: #ff9e00;
        letter-spacing: 4px;
        margin-top: -10px;
        margin-bottom: 40px;
        text-transform: uppercase;
    }

    /* BUTONLAR */
    div.stButton > button {
        background: linear-gradient(90deg, #ff7e5f, #feb47b);
        color: white;
        border: none;
        padding: 12px 35px;
        font-family: 'Oswald', sans-serif;
        font-size: 16px;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(255, 126, 95, 0.4);
        width: 100%;
    }
    
    /* TABLO DÜZENLEMELERİ (Editable tablo için) */
    .stDataFrame {
        background-color: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    div[data-testid="stDataEditor"] {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Supabase Bağlantısı
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ Secrets ayarları eksik!")
    st.stop()

def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# -----------------------------------------------------------------------------
# 2. FONKSİYONLAR
# -----------------------------------------------------------------------------

def trigger_webhook(username):
    webhook_url = "https://hook.eu1.make.com/ixxd5cuuqkhhkpd8sqn5soiyol0a952x"
    try:
        requests.get(f"{webhook_url}?username={username}")
        return True
    except:
        return False

def clear_database():
    try:
        supabase.table('influencers').delete().neq("username", "xxxx").execute()
        return True
    except Exception as e:
        st.error(f"Silme hatası: {e}")
        return False

def safe_json_parse(raw_data):
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

def calculate_roi_metrics(row, ad_cost, product_price):
    """
    KİŞİYE ÖZEL HESAPLAMA:
    Artık 'clicks' (tıklama) parametresi satırdan (row'dan) geliyor.
    """
    views = row.get('avg_views', 0)
    # Kişiye özel girilen tıklama sayısı (Tablodan gelir)
    clicks = row.get('Beklenen Tıklama', 0) 
    
    # İzlenme 0 ise hata vermesin
    if views <= 0:
        return pd.Series([0, 0, 0, 0], index=['CPM ($)', 'RPM ($)', 'Fark ($)', 'ROI (%)'])

    # 1. CPM (Maliyet)
    cpm = (ad_cost / views) * 1000
    
    # 2. RPM (Gelir) = (O Kişiye Özel Tıklama * Ürün Fiyatı / İzlenme) * 1000
    total_revenue = clicks * product_price
    rpm = (total_revenue / views) * 1000
    
    # 3. FARK
    diff = rpm - cpm
    
    # 4. ROI (%) = ((RPM - CPM) / CPM) * 100
    if olasi_gelir != 0:
        roi = ((influencer_ucreti - olasi_gelir) / olasi_gelir) * 100
    else:
        roi = 0 # Sıfıra bölünme hatasını önlemek için
    
    return pd.Series([cpm, rpm, diff, roi_percent], 
                     index=['CPM ($)', 'RPM ($)', 'Fark ($)', 'ROI (%)'])

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# --- GİRİŞ PANELİ ---
if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div class='glass-card' style='text-align: center;'>
                <h2 style='font-family:Oswald; text-transform:uppercase; font-size: 2rem; margin-bottom: 20px;'>
                    Giriş Yap
                </h2>
                <p style='opacity:0.7; font-size:0.9rem;'>ROI Analiz Platformuna Hoşgeldiniz</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            email = st.text_input("E-POSTA ADRESİ")
            password = st.text_input("ŞİFRE", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("SİSTEME GİRİŞ", type="primary", use_container_width=True):
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if user:
                        st.session_state['logged_in'] = True
                        st.success("Giriş Başarılı!")
                        time.sleep(0.5)
                        st.rerun()
                except:
                    st.error("Hatalı Giriş Bilgileri")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- ANA DASHBOARD ---
else:
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='color:#fff; padding-left:10px;'>KONTROL PANELİ</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("<div style='margin-bottom:20px;'>", unsafe_allow_html=True)
        new_u = st.text_input("YENİ ANALİZ (KULLANICI ADI)")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("ANALİZ ET 🚀", use_container_width=True):
            if new_u:
                trigger_webhook(new_u)
                st.info("Veri isteği gönderildi...")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h5 style='opacity:0.6; padding-left:10px;'>VERİ YÖNETİMİ</h5>", unsafe_allow_html=True)
        
        if st.button("TÜM LİSTEYİ SİL", use_container_width=True):
            if clear_database():
                st.toast("Liste Temizlendi!", icon="🗑️")
                time.sleep(1)
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ÇIKIŞ YAP", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ANA EKRAN İÇERİĞİ ---
    
    st.markdown("""
        <div>
            <h1 class='hero-title'>ROI ANALİZ</h1>
            <h3 class='subtitle'>INFLUENCER PERFORMANS SİMÜLATÖRÜ</h3>
        </div>
    """, unsafe_allow_html=True)

    # Girdi Alanları (Global Tıklama Kaldırıldı)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h4 style='margin:0; opacity:0.8;'>💸 MALİYET</h4>", unsafe_allow_html=True)
        # Maliyet şimdilik global, ama formül kişi başı izlenmeye bölerek CPM buluyor
        ad_cost = st.number_input("Influencer Bütçesi ($)", value=1000, step=100, label_visibility="collapsed")
    
    with col2:
        st.markdown("<h4 style='margin:0; opacity:0.8;'>🏷️ ÜRÜN</h4>", unsafe_allow_html=True)
        prod_price = st.number_input("Ürün Fiyatı ($)", value=30.0, step=5.0, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    # Veri İşleme
    response = supabase.table('influencers').select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Temel Veri Hazırlığı
        if 'Niche' not in df.columns:
            if 'niche' in df.columns: df['Niche'] = df['niche']
            else: df['Niche'] = "Genel"
        df['Niche'] = df['Niche'].fillna("Genel").replace("", "Genel")
        
        # İzlenmeleri Çek
        df['avg_views'] = df.apply(get_avg_views_from_json, axis=1)

        # ---------------------------------------------------------------------
        # YENİ: KİŞİYE ÖZEL TIKLAMA GİRİŞİ (Editable Dataframe)
        # ---------------------------------------------------------------------
        st.markdown("### 🖱️ TIKLAMA TAHMİNLERİNİ GİRİNİZ")
        st.info("Aşağıdaki tabloda **'Beklenen Tıklama'** sütununa her influencer için tahmininizi yazın, sonuçlar otomatik hesaplanacaktır.")

        # Eğer dataframede henüz bu sütun yoksa varsayılan 500 ata
        if 'Beklenen Tıklama' not in df.columns:
            df['Beklenen Tıklama'] = 500

        # Görüntülenecek ve Düzenlenecek Sütunlar
        editor_cols = ['username', 'Niche', 'avg_views', 'Beklenen Tıklama']
        
        # st.data_editor ile düzenlenebilir tablo oluşturuyoruz
        edited_df = st.data_editor(
            df[editor_cols],
            column_config={
                "username": st.column_config.TextColumn("Kullanıcı Adı", disabled=True),
                "Niche": st.column_config.TextColumn("Kategori", disabled=True),
                "avg_views": st.column_config.NumberColumn("Ort. İzlenme", disabled=True, format="%d"),
                "Beklenen Tıklama": st.column_config.NumberColumn("Beklenen Tıklama (Adet)", min_value=0, step=10, required=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed"
        )

        # ---------------------------------------------------------------------
        # HESAPLAMA (Düzenlenmiş veriyi kullanarak)
        # ---------------------------------------------------------------------
        # calculate_roi_metrics fonksiyonuna artık edited_df'deki satırları gönderiyoruz
        metrics = edited_df.apply(calculate_roi_metrics, args=(ad_cost, prod_price), axis=1)
        
        # Sonuçları ana tabloyla birleştir
        results_df = pd.concat([edited_df, metrics], axis=1)
        
        # Geçerli verileri filtrele (İzlenmesi olanlar)
        df_valid = results_df[results_df['avg_views'] > 0].copy()
        
        if not df_valid.empty:
            # Sıralamayı (RPM - CPM) Farkına göre yap
            df_valid = df_valid.sort_values(by="Fark ($)", ascending=False)
            
            # KAZANAN KARTI
            winner = df_valid.iloc[0]
            if winner['Fark ($)'] > 0:
                st.markdown(f"""
                <div class='glass-card' style='border-left: 5px solid #38ef7d; background: rgba(17, 153, 142, 0.2); margin-top: 20px;'>
                    <h2 style='font-family:Oswald; color:#38ef7d; margin:0;'>🏆 TAVSİYE EDİLEN: {winner['username']}</h2>
                    <p style='font-size: 1.2rem; margin-top:10px;'>
                        Girdiğiniz <b>{winner['Beklenen Tıklama']}</b> tıklama tahmini ile: <br>
                        ROI: <b style='color:white'>{winner['ROI (%)']:.1f}%</b> &nbsp;|&nbsp; 
                        RPM-CPM Farkı: <b style='color:white'>${winner['Fark ($)']:,.2f}</b>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='glass-card' style='border-left: 5px solid #ff4b1f; background: rgba(255, 75, 31, 0.1); margin-top: 20px;'>
                    <h3 style='color:#ff4b1f; margin:0;'>⚠️ Kârlı Senaryo Bulunamadı</h3>
                    <p>Girdiğiniz tıklama değerlerine göre RPM, maliyeti (CPM) karşılamıyor.</p>
                </div>
                """, unsafe_allow_html=True)

            # SONUÇ TABLOSU
            st.subheader("📋 SONUÇ RAPORU")
            cols = ['username', 'avg_views', 'Beklenen Tıklama', 'CPM ($)', 'RPM ($)', 'Fark ($)', 'ROI (%)']
            
            def safe_highlight(val):
                try:
                    if isinstance(val, str): return ''
                    color = 'rgba(56, 239, 125, 0.2)' if val > 0 else 'rgba(255, 75, 31, 0.2)'
                    return f'background-color: {color}; color: white;'
                except: return ''

            st.dataframe(
                df_valid[cols].style.format({
                    "avg_views": "{:,.0f}",
                    "Beklenen Tıklama": "{:,.0f}",
                    "CPM ($)": "${:.2f}",
                    "RPM ($)": "${:.2f}",
                    "Fark ($)": "${:+.2f}",
                    "ROI (%)": "{:.2f}%"
                }).applymap(safe_highlight, subset=['Fark ($)']),
                use_container_width=True,
                height=500
            )

        else:
            st.warning("Veri var ama videolu gönderi yok.")
    else:
        st.info("Listeniz boş. Soldan yeni analiz başlatın.")
