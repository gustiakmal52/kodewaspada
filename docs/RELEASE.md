# Gerbang distribusi 0.2.x

Dokumen ini menjaga agar paket publik konsisten dengan PolyForm Noncommercial, jalur lisensi komersial terpisah, dan bukti pengujian. Ia bukan pengganti teks `LICENSE` atau perjanjian pembeli.

## Risiko riwayat pengembangan

Dua commit pada checkout pengembangan lama sebelum `0.2.0` memakai lisensi MIT. Riwayat publik `main` sudah dimulai ulang dari snapshot bersih dan tidak memuat commit lama tersebut. **Jangan merge atau push branch pengembangan lama ke riwayat publik** jika syarat nonkomersial ingin dipertahankan. Lisensi yang sudah diterima pihak lain biasanya tidak dapat ditarik kembali hanya dengan mengganti berkas pada commit berikutnya.

Untuk pembaruan publik berikutnya, buat branch dari `origin/main` yang bersih. Branch lokal lama `codex/kodewaspada-v01` hanya arsip privat: jangan menggabungkannya ke branch publik dan jangan memakai `git push --all` atau `git push --mirror`. Jangan menghapus atau menulis ulang riwayat lama tanpa keputusan pemilik.

## Pemeriksaan sebelum berbagi

1. Pastikan root `LICENSE` dan `skills/kodewaspada/LICENSE` identik, berisi PolyForm Noncommercial 1.0.0, serta memuat `Required Notice: Copyright 2026 EL1Syum`.
2. Pastikan README, `COMMERCIAL-LICENSING.md`, metadata paket, dokumentasi produk/scanner, dan arsip tidak menyebut MIT atau mengklaim proyek sebagai open source OSI.
3. Jalankan seluruh tes, compile check, validator skill, evaluasi perilaku independen, dan pemindaian keamanan yang dicatat di `docs/QA.md`.
4. Dengan Python 3.11+ di Linux/WSL untuk script builder, bangun ZIP skill memakai `python3 scripts/build_skill_bundle.py`; jangan membuat ZIP manual. Builder menolak jalur output yang dapat diganti akun lain atau memiliki ACL tambahan, memeriksa digest kanonis pada byte lisensi yang benar-benar diarsipkan, mempertahankan descriptor/inode untuk penulisan/ukuran/hash, dan tidak menimpa output. ZIP baru dianggap lengkap setelah command sukses dan sidecar SHA-256 tersedia. Verifikasi sidecar serta isi satu folder teratas `kodewaspada/`.
5. Untuk snapshot source, gunakan hanya file terlacak pada commit rilis. Jangan sertakan `.git`, `.env`, output laporan, wheel lama, cache, atau artefak `0.1.x`.
6. Uji ekstraksi kedua arsip di direktori sementara dan jalankan validator dari hasil ekstraksi. Bandingkan daftar file serta checksum dengan source rilis.
7. Catat versi, commit source privat, checksum, lingkungan uji, hasil aktual, dan pemeriksaan yang dilewati. Jangan menyebut rilis siap bila gerbang yang wajib gagal.

## Lisensi komersial

Artefak publik selalu membawa PolyForm Noncommercial dan required notice yang sama. Bila pembeli memperoleh hak komersial, perjanjian terpisah harus menunjuk versi, commit, atau checksum yang dicakup; jangan mengganti lisensi di ZIP publik atau menganggap pembayaran tanpa kontrak sebagai izin.

Sebelum menerima kontribusi berhak cipta dari pihak luar, pastikan ada contributor agreement atau grant yang memang mengizinkan distribusi publik dan lisensi komersial terpisah. Issue, feedback, dan laporan bug bukan otomatis transfer hak cipta.

## Bahasa publikasi

Gunakan: **“KodeWaspada adalah skill source-available untuk review keamanan kode. Rilis publik mengizinkan penggunaan nonkomersial; lisensi komersial terpisah dapat diminta berdasarkan perjanjian tertulis.”**

Jangan gunakan: “open source”, “resmi OpenAI”, “didukung Daybreak”, “menjamin aman”, “nol false positive”, atau persentase akurasi yang diturunkan dari fixture.
