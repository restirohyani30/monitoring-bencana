import os
import streamlit as st
import pandas as pd
import psycopg2
import pymysql
from dotenv import load_dotenv
import plotly.express as px

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Dashboard Bencana Jawa Barat",
    page_icon="🌋",
    layout="wide"
)

load_dotenv()

# Fungsi Multi-DBMS Data Pipeline (Federation via Pandas)
@st.cache_data(ttl=300)
def load_and_federate_data():
    try:
        # 1. Kueri data transaksi dari PostgreSQL (Neon) - Direct Parameters
        conn_pg = psycopg2.connect(
            host="ep-round-poetry-b5p3t6cu.c-7.us-east-2.aws.neon.tech",
            port=5432,
            database="neondb",
            user="neondb_owner",
            password="npg_aZbBkpXtS20L",
            sslmode="require"
        )
        df_kejadian = pd.read_sql("SELECT * FROM kejadian_bencana", conn_pg)
        conn_pg.close()

        # 2. Kueri data master wilayah dari MySQL (Aiven)
        conn_mysql = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            ssl={'ca': os.getenv("MYSQL_SSL_CA")}
        )
        df_wilayah = pd.read_sql("SELECT * FROM master_wilayah", conn_mysql)
        conn_mysql.close()

        # Pastikan tipe data kolom kunci sama
        df_kejadian['kode_kabupaten_kota'] = df_kejadian['kode_kabupaten_kota'].astype(str)
        df_wilayah['kode_kabupaten_kota'] = df_wilayah['kode_kabupaten_kota'].astype(str)

        # 3. Data Federation (Penggabungan di layer aplikasi)
        df_merged = pd.merge(
            df_kejadian, 
            df_wilayah, 
            on='kode_kabupaten_kota', 
            how='inner'
        )

        return df_merged, "PostgreSQL (Kejadian) + MySQL (Master Wilayah)"

    except Exception as e:
        st.error(f"Gagal memuat Multi-DBMS Data Pipeline: {e}")
        return pd.DataFrame(), "Gagal Terhubung"

# Memuat Data Hasil Integrasi
df, source_info = load_and_federate_data()

# Header Utama
st.title("🌋 Dashboard Monitoring Bencana Alam Jawa Barat")
st.caption("Sistem Informasi Kebencanaan Terpadu (Multi-DBMS Data Pipeline)")
st.markdown("---")

if not df.empty:
    # --- SIDEBAR: Status & Filter ---
    st.sidebar.header("⚙️ Kontrol & Panel Filter")
    st.sidebar.success(f"🔗 Arsitektur DBMS Active:\n**{source_info}**")
    st.sidebar.markdown("---")

    # Filter Tahun
    tahun_list = ["Semua Tahun"] + sorted(list(df['tahun'].unique()))
    selected_tahun = st.sidebar.selectbox("Pilih Tahun:", tahun_list)

    # Filter Kabupaten/Kota (diambil dari hasil gabungan data master)
    kab_list = ["Semua Kabupaten/Kota"] + sorted(list(df['nama_kabupaten_kota'].unique()))
    selected_kab = st.sidebar.selectbox("Pilih Wilayah:", kab_list)

    # Filter Jenis Bencana
    bencana_list = ["Semua Jenis Bencana"] + sorted(list(df['jenis_bencana'].unique()))
    selected_bencana = st.sidebar.selectbox("Pilih Jenis Bencana:", bencana_list)

    # Filtering Dataframe
    filtered_df = df.copy()
    if selected_tahun != "Semua Tahun":
        filtered_df = filtered_df[filtered_df['tahun'] == selected_tahun]
    if selected_kab != "Semua Kabupaten/Kota":
        filtered_df = filtered_df[filtered_df['nama_kabupaten_kota'] == selected_kab]
    if selected_bencana != "Semua Jenis Bencana":
        filtered_df = filtered_df[filtered_df['jenis_bencana'] == selected_bencana]

    # --- METRICS / KPI CARDS ---
    m1, m2, m3, m4 = st.columns(4)

    total_kejadian = filtered_df['jumlah_kejadian'].sum()
    total_kab = filtered_df['nama_kabupaten_kota'].nunique()
    total_jenis = filtered_df['jenis_bencana'].nunique()
    tahun_aktif = selected_tahun if selected_tahun != "Semua Tahun" else "Multi-Tahun"

    m1.metric("Total Kejadian", f"{total_kejadian:,}")
    m2.metric("Kab/Kota Terdampak", total_kab)
    m3.metric("Variasi Bencana", total_jenis)
    m4.metric("Periode Dilihat", tahun_aktif)

    st.markdown("---")

    # --- GRAFIK BARIS 1 ---
    col_chart1, col_chart2 = st.columns([6, 4])

    with col_chart1:
        st.subheader("📊 Jumlah Kejadian per Jenis Bencana")
        df_bencana = filtered_df.groupby('jenis_bencana')['jumlah_kejadian'].sum().reset_index()
        fig_bar = px.bar(
            df_bencana.sort_values(by='jumlah_kejadian', ascending=False),
            x='jenis_bencana',
            y='jumlah_kejadian',
            color='jenis_bencana',
            text='jumlah_kejadian',
            labels={'jenis_bencana': 'Jenis Bencana', 'jumlah_kejadian': 'Total Kejadian'},
            template='plotly_white'
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(showlegend=False, xaxis_title="", height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        st.subheader("🍕 Proporsi Kejadian Bencana")
        fig_pie = px.pie(
            df_bencana,
            values='jumlah_kejadian',
            names='jenis_bencana',
            hole=0.4,
            template='plotly_white'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- GRAFIK BARIS 2 ---
    col_chart3, col_chart4 = st.columns([5, 5])

    with col_chart3:
        st.subheader("🏆 Top 10 Kabupaten/Kota Paling Terdampak")
        df_kab = filtered_df.groupby('nama_kabupaten_kota')['jumlah_kejadian'].sum().reset_index()
        df_top10 = df_kab.sort_values(by='jumlah_kejadian', ascending=True).tail(10)

        fig_top10 = px.bar(
            df_top10,
            x='jumlah_kejadian',
            y='nama_kabupaten_kota',
            orientation='h',
            text='jumlah_kejadian',
            color='jumlah_kejadian',
            color_continuous_scale='Reds',
            labels={'nama_kabupaten_kota': 'Kabupaten/Kota', 'jumlah_kejadian': 'Total Kejadian'}
        )
        fig_top10.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_top10, use_container_width=True)

    with col_chart4:
        st.subheader("📈 Tren Kejadian Bencana Antar Tahun")
        df_trend = df.groupby('tahun')['jumlah_kejadian'].sum().reset_index() if selected_tahun == "Semua Tahun" else filtered_df.groupby('tahun')['jumlah_kejadian'].sum().reset_index()

        fig_line = px.line(
            df_trend,
            x='tahun',
            y='jumlah_kejadian',
            markers=True,
            labels={'tahun': 'Tahun', 'jumlah_kejadian': 'Total Kejadian'},
            template='plotly_white'
        )
        fig_line.update_traces(line_color='#E74C3C', line_width=3, marker_size=8)
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    # --- TABEL HASIL FEDERASI ---
    st.markdown("---")
    st.subheader("📋 Eksplorasi Data Detail (Hasil Joining Multi-DBMS)")

    st.dataframe(filtered_df[['id', 'tahun', 'kode_kabupaten_kota', 'nama_kabupaten_kota', 'jenis_bencana', 'jumlah_kejadian']], use_container_width=True, hide_index=True)

    # Download CSV
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Terintegrasi (CSV)",
        data=csv_data,
        file_name='data_bencana_jabar_federated.csv',
        mime='text/csv'
    )