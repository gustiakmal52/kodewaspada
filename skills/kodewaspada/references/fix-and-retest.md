# Perbaikan minimal, bukti yang dapat diulang

Gunakan hanya ketika pengguna meminta Fix atau Retest; review biasa menghasilkan arahan, bukan perubahan aplikasi.

## Sebelum edit

1. Baca temuan/bukti dan pastikan kondisi masih berlaku pada checkout sekarang. Catat commit/diff bila tersedia, file yang akan disentuh, serta perubahan pengguna yang harus dipertahankan.
2. Cari semua caller dari fungsi/konfigurasi yang perlu diubah, kontrak API, fixture, dan tes terkait. Pilih titik kontrol bersama yang tepat; jangan memperluas refactor.
3. Periksa test runner dan script terkait sebelum menjalankannya. Pakai data sintetis serta service lokal khusus tes. Jangan memakai DB produksi, installer tak tepercaya, jaringan target, atau credential nyata.
4. Buat regresi minimum yang gagal karena root cause sebelum patch bila memungkinkan. Tes yang error karena dependency belum terpasang bukan reproduksi. Jika runtime tidak tersedia, catat penghalang dan jangan mengaku tes telah dijalankan.

## Saat edit

- Validasi/otorisasi di trust boundary dan semua jalur relevan; gunakan primitive framework yang sudah ada dan sesuai konteks.
- Pertahankan semantik API, format data, error handling, dan akses yang sah kecuali perubahan itu memang diperlukan untuk fix; jelaskan perubahan yang terlihat pengguna.
- Jangan menimpa pekerjaan pengguna, menghapus data/sejarah Git, menonaktifkan tes, menyembunyikan scanner finding, atau membundel upgrade besar yang tidak terkait.
- Untuk credential rotation, perubahan produksi, deployment, atau migrasi data, pisahkan rencana/patch dari eksekusi dan minta otorisasi aksi tersebut. Tidak perlu izin berulang untuk edit lokal yang memang sudah diminta.

## Retest dan serah terima

1. Jalankan skenario regresi dan kontrol sah. Untuk otorisasi, uji identitas/role berbeda serta isi/state; jangan hanya mengecek status HTTP.
2. Jalankan tes terkait dan build/type-check yang sesuai perubahan serta tersedia. Tidak perlu seluruh toolchain yang tidak relevan.
3. Tinjau diff final: scope sempit, tidak ada rahasia/bypass, caller/fixture/config/exports konsisten. Minta review independen untuk perubahan auth/data sensitif bila fasilitas tersedia; jangan mengarang review kedua.
4. Laporkan command aktual, exit code/ringkasan hasil, serta yang dilewati. Bedakan **patch diterapkan**, **retest lokal lulus**, dan **produksi terverifikasi**. Tes lokal tidak membuktikan deployment sudah berubah.
5. Jika retest gagal, perbaiki dalam scope atau nyatakan masalah masih terbuka. Jangan menghasilkan status lulus dari tes yang belum berjalan atau tidak menguji jalur yang diperbaiki.
