# 🌋 Dashboard Monitoring Bencana Alam Jawa Barat

Aplikasi web visualisasi interaktif terpadu yang dibangun untuk memonitor kejadian bencana alam di Provinsi Jawa Barat menggunakan arsitektur **Multi-DBMS Data Pipeline**.

---

## 🏗️ Ringkasan Arsitektur Basis Data (Multi-DBMS)

Sistem ini memisahkan penyimpanan data berdasarkan jenis dan karakteristik informasinya untuk menjaga kebersihan arsitektur (*separation of concerns*):

1. **DBMS 1 — Data Transaksi Kebencanaan**
   - **Engine**: PostgreSQL (Hosted via **Neon Serverless PostgreSQL**)
   - **Fungsi**: Menyimpan data transaksi kejadian bencana alam (`kejadian_bencana`) yang berisi catatan jumlah kejadian, jenis bencana, dan tahun pelaksanaan.
   - **Tabel**: `kejadian_bencana (id, tahun, kode_kabupaten_kota, jenis_bencana, jumlah_kejadian)`

2. **DBMS 2 — Data Master Wilayah**
   - **Engine**: MySQL (Hosted via **Aiven Cloud MySQL**)
   - **Fungsi**: Menyimpan data master/referensi wilayah (`master_wilayah`) untuk validasi nama kabupaten/kota resmi di Jawa Barat.
   - **Tabel**: `master_wilayah (kode_kabupaten_kota, nama_kabupaten_kota)`

---

## 🔄 Alur Integrasi Data Pipeline (Data Federation)

Proses manipulasi dan penggabungan data dilakukan secara terfederasi di tingkat aplikasi (*application-level data joining*):

1. **Extraction (Pengambilan Data)**:
   - Aplikasi mengambil data transaksi dari PostgreSQL Neon menggunakan konektor `psycopg2`.
   - Aplikasi mengambil data master wilayah dari MySQL Aiven menggunakan konektor `pymysql`.
2. **Transformation & Federation (Penggabungan)**:
   - Kedua dataset dimuat ke dalam struktur **Pandas DataFrame**.
   - Tipe data pada kolom kunci (`kode_kabupaten_kota`) diselaraskan ke format `String`.
   - Fungsi `pd.merge()` mengeksekusi operasi *Inner Join* menggunakan `kode_kabupaten_kota` sebagai *foreign key*.
3. **Loading & Caching**:
   - Hasil gabungan data disimpan sementara menggunakan decorator `@st.cache_data(ttl=300)` untuk mempercepat performa *rendering* antarmuka.

---

## 🎛️ Fitur Interaktivitas Antarmuka Visualisasi

Dashboard interaktif dibangun menggunakan **Streamlit** dan **Plotly Express** dengan fitur utama:

- **Filter Dinamis (Sidebar)**: Menyaring data secara real-time berdasarkan Tahun, Kabupaten/Kota, dan Jenis Bencana.
- **KPI Metrics Cards**: Ringkasan performa utama mencakup Total Kejadian, Jumlah Wilayah Terdampak, Variasi Bencana, dan Periode Aktif.
- **Visualisasi Grafik Interaktif**:
  - *Bar Chart*: Distribusi total kejadian berdasarkan jenis bencana.
  - *Pie Chart*: Proporsi persentase ancaman bencana.
  - *Horizontal Bar Chart*: Top 10 Kabupaten/Kota dengan tingkat dampak tertinggi.
  - *Line Chart*: Tren fluktuasi kejadian bencana antar tahun.
- **Eksplorasi Data Detail**: Tabel interaktif hasil *data federation* dilengkapi fitur pengunduhan data (*Download CSV*).

---

### 🛠️ Cara Menjalankan Aplikasi di Lokal

1. **Clone Repository:**
   ```bash
   git clone [https://github.com/restirohyani30/monitoring-bencana.git](https://github.com/restirohyani30/monitoring-bencana.git)
   cd monitoring-bencana

   ---

### 🔗 Validitas Data & Referensi Kode

* **Sumber Data Primer:** [Galura Data Jabar - Jumlah Kejadian Bencana Berdasarkan Jenis Bencana di Jawa Barat](https://galura.jabarprov.go.id/dataset/jumlah-kejadian-bencana-berdasarkan-jenis-bencana-di-jawa-barat)
* **Skrip Replikasi Database:** `seed.py`, `schema_postgres.sql`, dan `schema_mysql.sql`
* **Referensi Kode & Framework:**
  * [Streamlit Documentation](https://docs.streamlit.io)
  * [Plotly Express Python Documentation](https://plotly.com/python/)
  * [Neon PostgreSQL Documentation](https://neon.tech/docs)