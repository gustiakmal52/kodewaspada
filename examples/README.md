# Contoh untuk belajar, bukan aplikasi untuk dijalankan

`perlu-ditinjau/` sengaja berisi alur input ke API berisiko. Scanner hanya membaca
kode ini; jangan mengimpor atau menjalankannya di server. Tidak ada kredensial,
data pribadi, target eksternal, atau payload serangan di sini.

`kontrol-aman/` berisi kontrol negatif untuk tiga aturan saat ini: perintah tetap,
`execFile` tanpa shell, keluaran teks/JSX biasa, serta DOMPurify dari import yang
sesuai. “Kontrol aman” berarti aturan yang bersangkutan tidak seharusnya melapor,
bukan sertifikat bahwa seluruh contoh bebas risiko.

Komentar `ruleid:` dan `ok:` menjadi ekspektasi pengujian: baris berikutnya harus
terdeteksi atau tidak terdeteksi oleh ID aturan tersebut. Uji tidak mengeksekusi
JavaScript.
