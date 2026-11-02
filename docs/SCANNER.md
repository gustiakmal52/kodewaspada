# Scanner lokal opsional

Scanner ini adalah alat bantu untuk [skill KodeWaspada](../skills/kodewaspada/SKILL.md), bukan syarat untuk menggunakan skill. Ia memeriksa tiga jenis aliran data pada JavaScript/TypeScript dan menghasilkan kandidat untuk ditinjau. Skill tetap perlu membaca kode, memeriksa pembatasan akses, dan menilai bukti yang tidak tercakup scanner.

## Coba contoh lokal

Prasyarat: Python 3.10+, Semgrep Community Edition `1.179.0`, dan Linux/macOS (Windows melalui WSL). Pengujian awal dilakukan di Linux dengan Python 3.14.7; macOS dan WSL belum diuji. Scanner tidak membutuhkan API key atau akun.

Jika Semgrep belum ada, jalankan dari folder repo KodeWaspada untuk membuat lingkungan terpisah. Jangan memasang dependensi ke proyek yang akan diperiksa:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-engine.txt
```

Instalasi dependensi membutuhkan internet. Pemeriksaan memakai aturan lokal, dengan pengiriman metrics dan pemeriksaan versi dimatikan.

```bash
python3 -m kodewaspada scan examples/perlu-ditinjau --out outputs/contoh
```

Kode keluar `1` pada contoh tersebut berarti kandidat ditemukan, bukan kegagalan aplikasi. Buka `outputs/contoh/report.html` di browser; semua aset laporan tertanam sehingga tidak perlu server. Laporan juga tersedia sebagai Markdown dan JSON. CSS cetak tersedia untuk Ctrl+P atau ⌘+P, tetapi hasil cetak/PDF belum diuji menyeluruh.

Untuk proyek sendiri:

```bash
python3 -m kodewaspada scan /path/ke/proyek-anda --out outputs/review-pertama
```

Gunakan folder output baru setiap kali. Folder yang sudah ada atau berupa symlink ditolak; laporan lama tidak ditimpa. Folder output dibuat dengan izin `0700`. Hasil tetap dapat memuat nama proyek dan berkas yang sensitif; tinjau sebelum membagikannya.

## Tiga aturan

| Aturan | Aliran yang diperiksa | Batas penting |
| --- | --- | --- |
| KW001 | Input `req/request` menuju `child_process.exec` / `execSync` | Konvensi nama bukan bukti request HTTP; tidak mencakup semua API proses |
| KW002 | Input request/URL menuju `eval` / `Function` | Tidak membuktikan input dapat dieksploitasi; alias dinamis dapat terlewat |
| KW003 | Input request/URL menuju `innerHTML`, `dangerouslySetInnerHTML`, atau `res.send` | Konteks HTML, encoding, sanitizer, tipe respons, dan keterjangkauan tetap perlu ditinjau |

Aturan taint asli proyek ini melacak sumber input menuju operasi sensitif dalam cakupan Semgrep CE. Ini bukan analisis lengkap lintas fungsi/berkas. Nama parameter lain, validasi custom, alias dinamis, framework lain, dan konfigurasi sanitizer dapat menyebabkan kandidat salah atau masalah terlewat. Batas per aturan dijelaskan dalam laporan dan [panduan aturan](../kodewaspada/rules/README.md).

Semua hasil diberi status `needs_review`. Laporan menunjuk lokasi operasi yang ditemukan engine, tetapi belum menyertakan nomor baris sumber input (`source_line` belum tersedia). Telusuri sumber input secara manual sebelum menyimpulkan dampak.

Scanner ini belum memeriksa autentikasi/otorisasi, IDOR, RLS, logika pembayaran, SQL injection, semua bentuk XSS, malware, kredensial bocor, dependency CVE, riwayat Git, atau konfigurasi produksi. Tidak ada skor keamanan 0–100.

## Status dan exit code

| Exit | Makna |
| --- | --- |
| `0` | Analisis dalam cakupan selesai tanpa kandidat; bukan bukti aman |
| `1` | Analisis dalam cakupan selesai dan ada kandidat untuk ditinjau |
| `2` | Input/engine gagal atau analisis hanya sebagian; jangan gunakan sebagai kelulusan |

`completed` berarti engine melaporkan berkas yang disiapkan telah diperiksa dalam batas aturan. Folder tersembunyi, dependensi, dan hasil build tetap dikecualikan. Bahasa lain tidak didukung. Kendala parsing, aturan yang dilewati engine, atau batas pemrosesan membuat status `partial` atau `failed`, bukan hasil bersih.

Scanner bukan validator sintaks/build. Engine dapat menyaring awal berkas yang tidak relevan terhadap aturan tanpa mem-parsing seluruh isinya; error sintaks yang tidak dilaporkan engine dapat terlewat. Tetap jalankan build dan pengujian aplikasi secara terpisah.

## Cara engine dijalankan

Semgrep dipanggil sebagai executable terpisah dengan konfigurasi aturan lokal. Opsi yang digunakan meliputi:

```text
--oss-only --json --quiet
--metrics=off --disable-version-check
--disable-nosem --no-git-ignore --no-rewrite-rule-ids
--jobs=1 --timeout=5 --max-memory=512 --max-target-bytes=512000
```

Variabel lingkungan yang diwariskan dibatasi pada `PATH`, `HOME`, `LANG`, `LC_ALL`, dan `SYSTEMROOT`; token aplikasi serta opsi injeksi Python tidak diwariskan. Settings/log engine diarahkan ke direktori sementara. Engine yang berada di dalam proyek target ditolak agar executable dari proyek target tidak dijalankan.

## Privasi dan batas operasional

- Target dibaca dan disalin sementara untuk analisis; tidak diimpor, diinstal, dijalankan, atau diperbaiki otomatis. Salinan sementara dibersihkan setelah pemeriksaan.
- Tidak ada pemanggilan AI/backend dari scanner. Ini berbeda dari penggunaan skill: bila asisten AI membaca kode atau laporan, isinya mungkin diproses penyedia AI sesuai konfigurasi dan kebijakan layanannya. Scanner lokal tidak menjadikan sesi AI otomatis lokal.
- Laporan tidak memasukkan potongan kode mentah, nilai variabel, atau pesan error mentah engine. Nama proyek/berkas masih dapat bersifat sensitif. Ini bukan pemindai rahasia atau jaminan redaksi universal.
- Folder `.git`, folder tersembunyi, dependensi, hasil build, dan symlink tidak dianalisis. `.gitignore`, `.semgrepignore`, dan komentar `nosemgrep` proyek tidak diberi wewenang menyembunyikan temuan; kebijakan pemilihan berkas ada pada alat ini.
- Batas: 200 berkas, 512 KB per berkas, total 10 MB, 20.000 entri, 20 tingkat folder, dan waktu engine 120 detik. Output engine dibatasi 16 MB. Detail diagnostik staging dibatasi 1.000 item/256 KB dan kandidat laporan dibatasi 1.000 item/4 MB; bila salah satu batas tercapai, status menjadi `partial` dan laporan memuat penanda pemotongan. JSON, HTML, dan Markdown ditulis bergiliran untuk mengurangi puncak memori. Batas waktu per-rule 5 detik dan memori engine 512 MB adalah kontrol sumber daya, bukan jaminan kebal denial-of-service.
- Ekstensi yang didukung: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`. `.mts`/`.cts` dilaporkan belum didukung dan membuat cakupan tidak lengkap.
- Gunakan hanya pada proyek lokal yang boleh Anda baca dan yang tidak sedang diubah bersamaan. Versi ini bukan sandbox untuk menerima upload berbahaya dari publik atau memisahkan banyak pengguna.
- Tidak ada firewall jaringan otomatis. Konfigurasi metrics/version-check diperiksa, tetapi isolasi jaringan OS dan packet capture belum diuji. Instalasi dependensi dan membuka rujukan dapat memerlukan jaringan.

## Pengujian

Jalankan dari folder repo KodeWaspada:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q kodewaspada
python3 -m kodewaspada scan examples/kontrol-aman --out outputs/kontrol-baru
```

Contoh hanya untuk dibaca scanner. Jangan menjalankan berkas contoh JavaScript. Uji engine dapat dilewati bila Semgrep tidak terpasang; hasil tersebut bukan bukti kelayakan rilis. Fixture sintetis menguji 20 alur positif dan 10 kontrol negatif, bukan akurasi pada semua proyek. Bukti pengujian dan bagian yang belum diverifikasi dicatat di [QA](QA.md).

## Lisensi dan rujukan

Wrapper, panduan, dan aturan asli menggunakan [PolyForm Noncommercial License 1.0.0](../LICENSE) dengan `Required Notice: Copyright 2026 EL1Syum`. Anda boleh memakai, menyalin, mengubah, dan membagikannya untuk tujuan nonkomersial yang diizinkan lisensi. Penggunaan komersial atau penjualan kembali memerlukan lisensi tertulis terpisah dari pemegang hak. Ini lisensi source-available, bukan lisensi open-source OSI; teks lisensi lengkap tetap menjadi rujukan.

Semgrep adalah dependensi terpisah dengan lisensi upstream sendiri. Repo tidak menyertakan engine biner atau menyalin rule pack registry; periksa kewajiban dependensi sebelum mendistribusikan paket gabungan.

- [Semgrep: taint analysis](https://docs.semgrep.dev/writing-rules/data-flow/taint-mode/overview)
- [Semgrep: CLI](https://docs.semgrep.dev/cli-reference)
- [Semgrep: metrics](https://docs.semgrep.dev/metrics)

Rujukan menjelaskan engine, bukan sertifikasi atau dukungan resmi untuk KodeWaspada.
