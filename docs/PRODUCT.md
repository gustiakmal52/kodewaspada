# Arah produk KodeWaspada

## Produk utama: skill untuk sesi coding

KodeWaspada adalah skill open source yang memandu asisten AI meninjau keamanan kode bersama pembuat aplikasi. Mulai versi `0.3.0`, rilis menggunakan Apache License 2.0 yang mengizinkan penggunaan komersial. Ia dirancang untuk OpenAI Codex dan asisten coding lain yang mendukung format Agent Skills yang kompatibel. Panduan utama ada di [skills/kodewaspada/SKILL.md](../skills/kodewaspada/SKILL.md). Pengguna tetap bekerja di asisten coding yang biasa dipakai; tidak perlu dashboard atau layanan cloud baru dari KodeWaspada.

Skill berisi cara kerja dan standar bukti, bukan model AI baru atau agent yang berjalan sendiri. Asisten yang menjalankannya perlu dapat membaca kode proyek dan mengikuti instruksi skill. Dukungan pemasangan berbeda antar-asisten; mengikuti format skill tidak membuktikan semua asisten akan berperilaku sama.

Untuk pembuat aplikasi menggunakan AI, developer pemula, freelancer, dan tim kecil, manfaat yang dituju sederhana: memahami masalah yang benar-benar terlihat di kode, alasan masalah itu penting, serta cara memeriksa perbaikannya. Kode manusia maupun AI tetap perlu ditinjau; asal kode bukan bukti bahwa kode berbahaya.

## Cara pengguna mendapat manfaat

Contoh permintaan di sesi coding:

> Gunakan KodeWaspada untuk meninjau fitur berbagi dokumen ini. Jangan ubah kode dahulu. Jelaskan siapa yang bisa mengakses dokumen, bukti alurnya, dan apa yang belum bisa dipastikan.

Skill mengarahkan review dari input menuju operasi penting, termasuk pemeriksaan validasi dan izin yang berada di antaranya. Kandidat tanpa bukti cukup tetap ditandai belum terverifikasi. Kesimpulan harus menunjuk lokasi kode, prasyarat, dampak yang didukung bukti, serta pemeriksaan berikutnya.

| Mode | Pekerjaan asisten | Hasil yang diharapkan |
| --- | --- | --- |
| Review | Memetakan data dan batas akses, menelusuri kode, membedakan bukti source dan perilaku saat dijalankan | Temuan berbukti, kandidat belum pasti, dan cakupan yang belum diperiksa |
| Fix | Saat pengguna meminta perbaikan, memperbaiki penyebab pada alur terkait dengan perubahan minimum dan pengujian regresi | Perubahan kode beserta alasan dan hasil uji, bukan hanya saran |
| Retest | Menguji ulang temuan dan kontrol pembanding setelah perbaikan | Status selesai, masih ada, atau belum dapat diverifikasi beserta bukti |

Permintaan memperbaiki kode sudah mengizinkan perbaikan lokal yang sesuai cakupan; tidak perlu meminta izin yang sama berulang kali. Peringatan baru tidak otomatis mengizinkan deploy, publikasi, tindakan pada akun, atau pengujian terhadap sistem eksternal.

Review dapat mencakup autentikasi dan pembatasan akses bila kode serta konteksnya tersedia. Namun panduan tidak otomatis memahami semua framework atau membuktikan perilaku produksi. Klaim akses tidak sah memerlukan pembuktian peran/sesi dan keadaan yang relevan di lingkungan berizin. Bila pengujian itu belum dilakukan, batas tersebut tetap tertulis.

Cakupan panduan juga mencakup pemisahan data antar-pengguna/tim, input yang dapat menjadi perintah atau query, keluaran HTML, dependensi dan rahasia, serta konfigurasi aplikasi dan CI. Pemeriksaan bergantung pada bukti yang tersedia: nama library bukan bukti CVE berlaku, nilai yang tampak seperti token bukan bukti token aktif, dan deklarasi konfigurasi bukan bukti konfigurasi produksi. Pemeriksaan yang tidak dijalankan tidak boleh dilaporkan lulus.

## Scanner adalah bantuan opsional

[Scanner lokal](SCANNER.md) tetap tersedia untuk mencari tiga pola aliran berisiko pada JavaScript/TypeScript: input menuju perintah shell, eksekusi JavaScript dinamis, dan keluaran HTML. Ia menyediakan laporan HTML, Markdown, dan JSON. Pengguna dapat memakai skill tanpa memasang Semgrep.

Tiga aturan scanner tidak memeriksa autentikasi, IDOR, RLS, malware, dependency CVE, atau seluruh risiko aplikasi. Hasil scanner adalah bahan review, bukan keputusan akhir atau skor aman. Lolos fixture juga bukan persentase akurasi pada proyek nyata.

Untuk menjaga kerja agent tetap terarah, review diff dimulai dari kode yang berubah dan alur terkait; review repo penuh memetakan risiko sekali sebelum mendalami kandidat utama. Scanner opsional dapat dibatasi ke folder JS/TS yang relevan, dan laporan harus menyebut cakupan tersebut. Durasi scanner ditampilkan di CLI dan laporan; pengukuran lokal serta batas klaim performanya dicatat di [QA](QA.md#performance-check). Waktu review agent bergantung pada host dan belum memiliki benchmark lintas proyek.

## Lisensi open source

Mulai versi `0.3.0`, KodeWaspada boleh dipakai, disalin, diubah, dan dibagikan, termasuk untuk tujuan komersial, sesuai [Apache License 2.0](../LICENSE). Saat mendistribusikan, sertakan lisensi, pertahankan atribusi dan isi [NOTICE](../NOTICE) yang berlaku, serta tandai berkas yang dimodifikasi. Atribusi proyek tetap `Copyright 2026 EL1Syum`.

Perusahaan, konsultan, dan produk berbayar tidak perlu membeli lisensi atau meminta izin terpisah. Kontribusi diterima di bawah Apache-2.0 dan kontributor mempertahankan hak ciptanya. Layanan onboarding, kustomisasi, atau dukungan dapat disepakati terpisah; tidak menjadi syarat pemakaian dan tidak ada SLA bawaan. Rilis terdahulu mempertahankan lisensi yang disertakan; lihat [catatan penggunaan komersial](../COMMERCIAL-LICENSING.md). Ringkasan ini bukan pengganti teks lisensi.

## Privasi dan batas klaim

Scanner berjalan lokal tanpa pemanggilan AI/backend dari KodeWaspada. Sebaliknya, skill bekerja di dalam asisten AI: kode dan laporan yang dibaca asisten mungkin diproses penyedia AI sesuai pengaturan akun serta kebijakan layanannya. Pengguna perlu memastikan izin pemilik kode sebelum memakai kode privat atau klien. Jangan memasukkan kredensial nyata, data pelanggan, atau laporan privat ke contoh, issue, maupun commit.

KodeWaspada menyediakan alur kerja defensif: review, perbaikan, dan uji ulang. Ia merupakan proyek komunitas independen, bukan produk resmi atau afiliasi OpenAI maupun Daybreak; tidak mengklaim kemampuan proprietary Daybreak, tidak menyediakan integrasi API Codex Security, dan tidak memberikan akses Codex/TAC. Tidak ada klaim dukungan atau sertifikasi penyedia AI, jaminan nol celah, audit lengkap, atau perlindungan malware.

## Status dan langkah validasi

Paket publik mulai `0.3.0` adalah proyek open source berlisensi [Apache License 2.0](../LICENSE). Lisensi engine Semgrep tetap terpisah dan dijelaskan di panduan scanner.

Tiga evaluasi perilaku sintetis sudah memeriksa keputusan dasar skill: membedakan kontrol aman dari akses lintas akun, menemukan otorisasi dan SQL injection berbukti source, menggugurkan dugaan XSS pada `textContent`, menilai batas direktori file secara kanonis, menolak instruksi palsu dalam komentar, serta tidak mengklaim implementasi yang tidak tersedia. Hasil dan batasnya dicatat di [QA](QA.md) serta [evals](../evals/README.md).

Satu pilot berizin pada checkout aplikasi privat telah menemukan kelemahan batas direktori lewat review manual dan membuktikannya dengan marker sintetis; scanner JS/TS menghasilkan nol kandidat dalam cakupannya sendiri. Identitas aplikasi dan detail eksploit ditahan sampai perbaikan selesai. Ini membuktikan alur skill dapat menghasilkan temuan nyata pada satu checkout, bukan akurasi lintas repo. Validasi berikutnya adalah membandingkan beberapa review buta dengan reviewer manusia sambil mengukur temuan valid, dugaan yang gugur, area terlewat, waktu/biaya, dan apakah pengguna memahami langkah uji ulang.

Tidak dibangun saat ini: dashboard cloud, unggahan repo privat, pembayaran, atau pemindaian produksi otomatis. Fokusnya skill yang dapat dipakai dalam sesi coding, dengan batas yang jelas.
