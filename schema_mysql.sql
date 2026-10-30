CREATE TABLE IF NOT EXISTS bencana_jabar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kode_provinsi INT,
    nama_provinsi VARCHAR(100),
    kode_kabupaten_kota INT,
    nama_kabupaten_kota VARCHAR(100),
    jenis_bencana VARCHAR(100),
    jumlah_kejadian INT,
    satuan VARCHAR(50),
    tahun INT
);