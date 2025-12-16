import streamlit as st

def main():
    st.title("Influencer ROI Hesaplayıcı (Özel Formül)")
    
    st.write("Aşağıdaki değerleri girerek ROI hesaplaması yapabilirsiniz.")

    # --- GİRDİ ALANLARI ---
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            influencer_ucreti = st.number_input(
                "Influencer'a Verilecek Tutar (TL)", 
                min_value=0.0, 
                value=5000.0,
                step=100.0
            )
            urun_fiyati = st.number_input(
                "Ürün Satış Fiyatı (TL)", 
                min_value=0.0, 
                value=250.0,
                step=10.0
            )
            
        with col2:
            tiklanma = st.number_input(
                "Tahmini Tıklanma Sayısı (Adet)", 
                min_value=1, 
                value=1000,
                step=10
            )
            # Dönüşüm oranı opsiyonel, tıklanma üzerinden gidildiği için şimdilik pasif bırakılabilir
            # ya da tıklanma * dönüşüm = satış adedi gibi düşünülebilir.
            # Senin formülünde direkt "Tıklanma x Fiyat" olduğu için buna sadık kalıyoruz.

    st.divider()

    # --- HESAPLAMA BUTONU VE MANTIK ---
    if st.button("ROI Hesapla"):
        
        # 1. Geliri (Payda) Hesapla
        # Formüldeki: (tıklanma x ürün fiyatı)
        olasi_gelir = tiklanma * urun_fiyati
        
        # 2. ROI Hesapla (SENİN İSTEDİĞİN ÖZEL FORMÜL)
        # Formül: ((Maliyet - Gelir) / Gelir) * 100
        # roi = ((inlencera verielcek tutar - (tıklanma x ürün fiyatı)) / (tıklanma x ürün fiyatı)) x 100
        
        if olasi_gelir > 0:
            roi = ((influencer_ucreti - olasi_gelir) / olasi_gelir) * 100
            
            # --- SONUÇ GÖSTERİMİ ---
            st.subheader(f"ROI Sonucu: %{roi:.2f}")
            
            st.info(f"Hesaplanan Gelir (Payda): {olasi_gelir} TL")
            
            # Yorumlama (Bu formüle göre):
            # Eğer Maliyet > Gelir ise sonuç POZİTİF çıkar (Zarar durumu / Pahalıya mal olma)
            # Eğer Maliyet < Gelir ise sonuç NEGATİF çıkar (Kârlı durum)
            if roi > 0:
                st.warning("Sonuç Pozitif (>0): Maliyet gelirden yüksek. (Zarar/Riskli)")
            elif roi < 0:
                st.success("Sonuç Negatif (<0): Gelir maliyetten yüksek. (Kârlı)")
            else:
                st.info("Sonuç 0: Maliyet ve Gelir eşit (Başa baş).")
                
        else:
            st.error("Hata: Tıklanma veya Ürün Fiyatı 0 olamaz (Sıfıra bölünme hatası).")

if __name__ == "__main__":
    main()
