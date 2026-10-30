import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import pymysql
from dotenv import load_dotenv

load_dotenv()

# 1. Baca File CSV
csv_file = 'od_18727_jumlah_kejadian_bencana_berdasarkan_jenis_bencana_v1.csv'
print("📌 Membaca file CSV...")
df = pd.read_csv(csv_file)

# 2. Upload Data Master Wilayah ke MySQL (Aiven)
print("⏳ Mengirim master_wilayah ke MySQL (Aiven)...")
conn_mysql = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    ssl={'ca': os.getenv("MYSQL_SSL_CA")}
)
cursor_mysql = conn_mysql.cursor()

cursor_mysql.execute("""
CREATE TABLE IF NOT EXISTS master_wilayah (
    kode_kabupaten_kota VARCHAR(50) PRIMARY KEY,
    nama_kabupaten_kota VARCHAR(100)
);
""")

df_wilayah = df[['kode_kabupaten_kota', 'nama_kabupaten_kota']].drop_duplicates()

for _, row in df_wilayah.iterrows():
    cursor_mysql.execute("""
    INSERT INTO master_wilayah (kode_kabupaten_kota, nama_kabupaten_kota)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE nama_kabupaten_kota = VALUES(nama_kabupaten_kota);
    """, (str(row['kode_kabupaten_kota']), row['nama_kabupaten_kota']))

conn_mysql.commit()
conn_mysql.close()
print("✅ Data Master Wilayah berhasil disimpan di MySQL!")

# 3. Upload Data Kejadian ke PostgreSQL (Neon) - Optimasi Bulk Insert
print("⏳ Mengirim kejadian_bencana ke PostgreSQL (Neon)...")
conn_pg = psycopg2.connect(
    host="ep-round-poetry-b5p3t6cu.c-7.us-east-2.aws.neon.tech",
    port=5432,
    database="neondb",
    user="neondb_owner",
    password="npg_aZbBkpXtS20L",
    sslmode="require",
    connect_timeout=30  # Mencegah hang jika server lambat merespons
)
cursor_pg = conn_pg.cursor()

cursor_pg.execute("""
CREATE TABLE IF NOT EXISTS kejadian_bencana (
    id SERIAL PRIMARY KEY,
    tahun INT,
    kode_kabupaten_kota VARCHAR(50),
    jenis_bencana VARCHAR(100),
    jumlah_kejadian INT
);
""")

cursor_pg.execute("TRUNCATE TABLE kejadian_bencana;")

# Format data menjadi tuple list untuk dikirim sekaligus
records = [
    (int(row['tahun']), str(row['kode_kabupaten_kota']), str(row['jenis_bencana']), int(row['jumlah_kejadian']))
    for _, row in df.iterrows()
]

# Bulk Insert dalam 1 kali kirim
insert_query = """
INSERT INTO kejadian_bencana (tahun, kode_kabupaten_kota, jenis_bencana, jumlah_kejadian)
VALUES %s;
"""
execute_values(cursor_pg, insert_query, records)

conn_pg.commit()
conn_pg.close()
print("✅ Data Kejadian Bencana berhasil disimpan di PostgreSQL!")
print("\n🎉 Proses Inisialisasi Database Selesai!")