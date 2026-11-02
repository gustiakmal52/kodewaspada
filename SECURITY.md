# Kebijakan keamanan KodeWaspada

KodeWaspada membantu review keamanan, sehingga laporan tentang kelemahan pada skill, scanner, aturan, renderer laporan, atau proses paket perlu ditangani dengan bukti dan tanpa mengekspos data pengguna.

## Versi yang didukung

Versi `0.2.x` adalah jalur rilis yang sedang disiapkan. Versi `0.1.x` adalah prototipe lokal dan tidak didukung untuk distribusi. Status pra-rilis ini tidak menjanjikan SLA atau sertifikasi keamanan.

## Melaporkan masalah

Setelah repo publik tersedia, gunakan **GitHub Security Advisory → Report a vulnerability** jika fitur tersebut aktif. Bila kanal privat itu belum tersedia, hubungi pemilik melalui kanal tempat Anda menerima paket dan berikan ringkasan minimum terlebih dahulu. Jangan menaruh credential, kode klien, data pribadi, atau detail celah yang belum diperbaiki di issue publik.

Laporan yang berguna memuat:

- versi/commit dan komponen yang terdampak;
- lokasi source serta alur input → kontrol → operasi → efek;
- langkah reproduksi lokal dengan data sintetis;
- hasil aktual dan kontrol pembanding;
- dampak yang sudah dibuktikan serta bagian yang masih belum pasti.

Jangan menguji sistem pihak lain, credential nyata, atau target produksi atas nama proyek ini. Temuan dari pola string atau output scanner tetap kandidat sampai alur dan kontrolnya diverifikasi.

## Respons dan perbaikan

Pemilik akan menilai bukti, meminta konteks minimum bila perlu, dan mengklasifikasikan temuan sebagai terbukti, perlu verifikasi, atau gugur. Jadwal respons/perbaikan belum memiliki SLA. Publikasi terkoordinasi hanya dilakukan setelah perbaikan atau mitigasi tersedia dan tidak membocorkan data sensitif.

Lisensi nonkomersial proyek tetap berlaku pada penggunaan dan distribusi kode; pelaporan kerentanan tidak memberikan hak komersial tambahan.
