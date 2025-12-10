import streamlit as st
import feedparser
import pandas as pd
import time
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="LPG & Akaryakıt Medya Takip",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- FONKSİYONLAR ---
def haberleri_getir(kelimeler, gun_sayisi):
    tum_veriler = []

    # İlerleme çubuğu
    progress_bar = st.progress(0)
    status_text = st.empty()

    toplam_kelime = len(kelimeler)

    for i, kelime in enumerate(kelimeler):
        # Yüzdelik hesapla ve güncelle
        oran = (i + 1) / toplam_kelime
        progress_bar.progress(oran)
        status_text.markdown(f"**Taranıyor:** `{kelime}` ({i + 1}/{toplam_kelime})")

        # URL encoding (boşlukları %20 yap)
        url_kelime = kelime.replace(" ", "%20")

        # Google News RSS (when:Xd = Son X gün)
        rss_url = f"https://news.google.com/rss/search?q={url_kelime}+when:{gun_sayisi}d&hl=tr&gl=TR&ceid=TR:tr"

        try:
            feed = feedparser.parse(rss_url)
            # Eğer feed boş değilse
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

        time.sleep(0.3)  # Google'ı engellememek için kısa bekleme

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(tum_veriler)


# --- ARAYÜZ TASARIMI ---

# Yan Menü (Sidebar)
with st.sidebar:
    st.header("⚙️ Ayarlar")

    st.markdown("### 📅 Zaman Aralığı")
    # Varsayılan 3 gün olarak ayarlı, kullanıcı değiştirebilir
    gun_secimi = st.slider(
        "Kaç günlük haberler taransın?",
        min_value=1,
        max_value=30,
        value=3,  # VARSAYILAN: 3 Gün
        help="Google Haberler üzerinde geriye dönük kaç gün taranacağını belirler."
    )
    st.caption(f"Şu anki ayar: **Son {gun_secimi} gün** içerisindeki haberler.")

    st.markdown("---")

    st.markdown("### 📋 Takip Listesi")

    # --- GÜNCELLENEN KISIM: SADECE İSTEDİĞİN 5 KELİME ---
    varsayilan_list = [
        "LPG",
        "OTOGAZ",
        "TÜPGAZ",
        "MİLANGAZ",
        "LİKİTGAZ"
    ]

    # Kullanıcı listeyi düzenleyebilsin diye text_area
    secilenler_text = st.text_area(
        "Listeyi düzenleyebilirsiniz (Her satıra bir kelime):",
        value="\n".join(varsayilan_list),
        height=200
    )

    # Text alanından listeye çevir
    secilenler_listesi = [x.strip() for x in secilenler_text.split('\n') if x.strip()]

    analiz_butonu = st.button("Analizi Başlat", type="primary", use_container_width=True)

    st.info(f"Listede {len(secilenler_listesi)} adet anahtar kelime var.")

# Ana Ekran
st.title("🔥 LPG & Akaryakıt Haber Takip Paneli")
st.markdown(f"""
Bu sistem, belirlediğiniz anahtar kelimelerle ilgili **son {gun_secimi} gün** içinde çıkan haberleri Google News üzerinden tarar.
""")

if analiz_butonu:
    with st.spinner(f'Son {gun_secimi} günün verileri taranıyor, lütfen bekleyin...'):
        df = haberleri_getir(secilenler_listesi, gun_secimi)

    if not df.empty:
        # Metrikler
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Haber", len(df), delta=f"{gun_secimi} Günlük")
        c2.metric("Benzersiz Kaynak", df['Kaynak'].nunique())

        # En çok geçen konuyu bul
        try:
            en_cok_konu = df['Konu'].value_counts().idxmax()
            c3.metric("Gündemdeki Konu", en_cok_konu)
        except:
            c3.metric("Gündemdeki Konu", "-")

        st.divider()

        # Sekmeler
        tab1, tab2 = st.tabs(["📄 Haber Listesi", "📊 Grafik Analiz"])

        with tab1:
            st.dataframe(
                df[['Konu', 'Başlık', 'Kaynak', 'Tarih']],
                use_container_width=True,
                height=500,
                hide_index=True
            )

            # Linkler
            with st.expander("🔗 Haber Linklerine Git"):
                for index, row in df.iterrows():
                    st.markdown(f"**{row['Konu']}**: [{row['Başlık']}]({row['Link']}) - *{row['Kaynak']}*")

        with tab2:
            st.subheader("Hangi konu hakkında ne kadar haber var?")
            chart_data = df['Konu'].value_counts()
            st.bar_chart(chart_data)

        # Excel İndirme Butonu
        tarih_str = datetime.now().strftime("%Y-%m-%d")
        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="📥 Sonuçları Excel (CSV) Olarak İndir",
            data=csv,
            file_name=f'LPG_Haber_Analizi_{tarih_str}.csv',
            mime='text/csv',
        )

    else:
        st.warning(f"Son {gun_secimi} gün içinde belirtilen kelimelerle ilgili haber bulunamadı.")
else:
    st.info("👈 Başlamak için sol taraftan 'Analizi Başlat' butonuna basın.")