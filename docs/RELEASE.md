# Gerbang distribusi 0.2.x

Dokumen ini menjaga agar paket yang dibagikan konsisten dengan lisensi nonkomersial dan bukti pengujian. Ia bukan pengganti teks `LICENSE`.

## Risiko riwayat pengembangan

Dua commit pengembangan lokal sebelum `0.2.0` memakai lisensi MIT. Repo belum memiliki remote dan belum dipublikasikan, tetapi **riwayat lokal tersebut tidak boleh didorong ke repo publik** jika syarat nonkomersial ingin dipertahankan. Lisensi yang sudah diterima pihak lain biasanya tidak dapat ditarik kembali hanya dengan mengganti berkas pada commit berikutnya.

Untuk publikasi pertama, gunakan snapshot bersih `0.2.0` tanpa folder `.git`, lalu buat riwayat baru yang dimulai dari snapshot berlisensi PolyForm Noncommercial 1.0.0. Simpan repo pengembangan lokal sebagai arsip privat; jangan menghapus atau menulis ulang riwayatnya tanpa keputusan pemilik.

## Pemeriksaan sebelum berbagi

1. Pastikan root `LICENSE` dan `skills/kodewaspada/LICENSE` identik, berisi PolyForm Noncommercial 1.0.0, serta memuat `Required Notice: Copyright 2026 EL1Syum`.
2. Pastikan README, metadata paket, dokumentasi produk/scanner, dan arsip tidak menyebut MIT atau mengklaim proyek sebagai open source OSI.
3. Jalankan seluruh tes, compile check, validator skill, evaluasi perilaku independen, dan pemindaian keamanan yang dicatat di `docs/QA.md`.
4. Dengan Python 3.11+ di Linux/WSL untuk script builder, bangun ZIP skill memakai `python3 scripts/build_skill_bundle.py`; jangan membuat ZIP manual. Builder menolak jalur output yang dapat diganti akun lain atau memiliki ACL tambahan, memeriksa digest kanonis pada byte lisensi yang benar-benar diarsipkan, mempertahankan descriptor/inode untuk penulisan/ukuran/hash, dan tidak menimpa output. ZIP baru dianggap lengkap setelah command sukses dan sidecar SHA-256 tersedia. Verifikasi sidecar serta isi satu folder teratas `kodewaspada/`.
5. Untuk snapshot source, gunakan hanya file terlacak pada commit rilis. Jangan sertakan `.git`, `.env`, output laporan, wheel lama, cache, atau artefak `0.1.x`.
6. Uji ekstraksi kedua arsip di direktori sementara dan jalankan validator dari hasil ekstraksi. Bandingkan daftar file serta checksum dengan source rilis.
7. Catat versi, commit source privat, checksum, lingkungan uji, hasil aktual, dan pemeriksaan yang dilewati. Jangan menyebut rilis siap bila gerbang yang wajib gagal.

## Bahasa publikasi

Gunakan: **“KodeWaspada adalah skill source-available untuk review keamanan kode dengan penggunaan nonkomersial.”**

Jangan gunakan: “open source”, “resmi OpenAI”, “didukung Daybreak”, “menjamin aman”, “nol false positive”, atau persentase akurasi yang diturunkan dari fixture.
