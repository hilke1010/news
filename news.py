import streamlit as st
import feedparser
import pandas as pd
import time
from datetime import datetime

# --- SAYFA AYARLARI (En başta olmalı) ---
st.set_page_config(
    page_title="LPG & Akaryakıt Medya Takip",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GÜVENLİK BİLGİLERİ ---
KULLANICI_ADI_DOGRU = "Likitgaz2025"
SIFRE_DOGRU = "LKTKTL25"

# --- OTURUM KONTROLÜ ---
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False

# --- GİRİŞ EKRANI FONKSİYONU ---
def giris_formu():
    st.markdown("## 🔒 Güvenli Giriş")
    st.markdown("Devam etmek için lütfen giriş yapınız.")
    
    kullanici = st.text_input("Kullanıcı Adı")
    sifre = st.text_input("Parola", type="password")
    
    giris_butonu = st.button("Giriş Yap", type="primary")

    if giris_butonu:
        if kullanici == KULLANICI_ADI_DOGRU and sifre == SIFRE_DOGRU:
            st.session_state['giris_yapildi'] = True
            st.rerun() # Sayfayı yenileyerek uygulamayı aç
        else:
            st.error("Hatalı kullanıcı adı veya parola!")

# --- ANA UYGULAMA FONKSİYONLARI ---
def haberleri_getir(kelimeler, gun_sayisi):
    tum_veriler = []
    
    # İlerleme çubuğu
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    toplam_kelime = len(kelimeler)
    
    for i, kelime in enumerate(kelimeler):
        oran = (i + 1) / toplam_kelime
        progress_bar.progress(oran)
        status_text.markdown(f"**Taranıyor:** `{kelime}` ({i+1}/{toplam_kelime})")
        
        url_kelime = kelime.replace(" ", "%20")
        
        # Google News RSS
        rss_url = f"https://news.google.com/rss/search?q={url_kelime}+when:{gun_sayisi}d&hl=tr&gl=TR&ceid=TR:tr"
        
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                for entry in feed.entries:
                    tum_veriler.append({
                        "Konu": kelime,
                        "Başlık": entry.title,
                        "Kaynak": entry.source.title if 'source' in entry else "Google News",
                        "Tarih": entry.published,
                        "Link": entry.link
                    })
        except Exception as e:
            st.error(f"Hata oluştu ({kelime}): {e}")
            
        time.sleep(0.3)

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(tum_veriler)

def ana_uygulama():
    # --- YAN MENÜ ---
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        st.markdown("### 📅 Zaman Aralığı")
        gun_secimi = st.slider(
            "Kaç günlük haberler taransın?",
            min_value=1,
            max_value=30,
            value=3, # Varsayılan: 3 Gün
            help="Geriye dönük kaç gün taranacağını belirler."
        )
        st.caption(f"Şu anki ayar: **Son {gun_secimi} gün**.")

        st.markdown("---")
        st.markdown("### 📋 Takip Listesi")
        
        # VARSAYILAN LİSTE
        varsayilan_list = [
            "LPG", 
            "OTOGAZ", 
            "TÜPGAZ", 
            "MİLANGAZ", 
            "LİKİTGAZ"
        ]
        
        secilenler_text = st.text_area(
            "Listeyi düzenleyebilirsiniz:",
            value="\n".join(varsayilan_list),
            height=200
        )
        
        secilenler_listesi = [x.strip() for x in secilenler_text.split('\n') if x.strip()]
        
        analiz_butonu = st.button("Analizi Başlat", type="primary", use_container_width=True)
        
        # Çıkış Butonu
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['giris_yapildi'] = False
            st.rerun()

    # --- ANA EKRAN İÇERİĞİ ---
    st.title("🔥 LPG & Akaryakıt Haber Takip Paneli")
    st.markdown(f"**Hoşgeldiniz.** Bu sistem **son {gun_secimi} gün** içinde çıkan haberleri tarar.")

    if analiz_butonu:
        with st.spinner(f'Son {gun_secimi} günün verileri taranıyor...'):
            df = haberleri_getir(secilenler_listesi, gun_secimi)
        
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Haber", len(df), delta=f"{gun_secimi} Günlük")
            c2.metric("Benzersiz Kaynak", df['Kaynak'].nunique())
            try:
                en_cok_konu = df['Konu'].value_counts().idxmax()
                c3.metric("Gündemdeki Konu", en_cok_konu)
            except:
                c3.metric("Gündemdeki Konu", "-")
            
            st.divider()
            
            tab1, tab2 = st.tabs(["📄 Haber Listesi", "📊 Grafik Analiz"])
            
            with tab1:
                st.dataframe(df[['Konu', 'Başlık', 'Kaynak', 'Tarih']], use_container_width=True, height=500, hide_index=True)
                with st.expander("🔗 Linkleri Göster"):
                    for index, row in df.iterrows():
                        st.markdown(f"**{row['Konu']}**: [{row['Başlık']}]({row['Link']}) - *{row['Kaynak']}*")

            with tab2:
                st.subheader("Konu Dağılımı")
                st.bar_chart(df['Konu'].value_counts())

            tarih_str = datetime.now().strftime("%Y-%m-%d")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Excel (CSV) İndir", data=csv, file_name=f'LPG_Analiz_{tarih_str}.csv', mime='text/csv')
        else:
            st.warning("Belirtilen kriterlerde haber bulunamadı.")
    else:
        st.info("👈 Analizi başlatmak için butona tıklayın.")

# --- PROGRAM AKIŞI ---
if not st.session_state['giris_yapildi']:
    giris_formu()
else:
    ana_uygulama()
