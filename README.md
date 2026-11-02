# KodeWaspada

**Security review untuk developer yang ngoding dengan AI: cari bukti, perbaiki akar masalah, lalu retest.**

[![Source Available](https://img.shields.io/badge/license-PolyForm%20Noncommercial-6f42c1)](LICENSE)
[![Security Review](https://img.shields.io/badge/focus-AppSec%20%2B%20AI%20Coding-0a7f5a)](#yang-dibantu)
[![Language](https://img.shields.io/badge/docs-Bahasa%20Indonesia-dc2626)](#kodewaspada)

KodeWaspada adalah **Agent Skill blue-team** untuk OpenAI Codex dan coding assistant yang mendukung format Agent Skills kompatibel. Ia membantu agent menelusuri alur kode, membedakan dugaan dari bukti, memperbaiki root cause saat diminta, dan menguji ulang hasilnya.

### Mulai dalam 30 detik

Salin folder [`skills/kodewaspada`](skills/kodewaspada) ke direktori skill proyek, lalu gunakan:

```text
$kodewaspada Review keamanan proyek ini sebelum deploy.
Prioritaskan akses data antar pengguna dan input yang berbahaya.
Tunjukkan bukti, dampak, dan batas analisis. Jangan ubah kode dulu.
```

**Kenapa beda dari prompt security biasa?**

- Evidence-first: temuan harus punya lokasi dan alur kode yang jelas.
- False-positive aware: kontrol yang sudah benar harus menggugurkan dugaan.
- Fix-aware: patch hanya saat diminta dan fokus ke akar masalah.
- Retest-aware: tidak mengklaim lulus sebelum pengujian benar-benar dijalankan.
- Ada scanner opsional untuk beberapa pola taint JS/TS, tetapi skill tetap bisa dipakai tanpa Python atau Semgrep.

> Proyek komunitas independen. Bukan produk resmi, afiliasi, dukungan, sertifikasi, atau integrasi keamanan dari OpenAI maupun Daybreak.

Status: **early release / source-available nonkomersial**. Skill adalah instruksi untuk agent, bukan model AI baru dan bukan jaminan aplikasi aman.

Jika proyek ini membantu workflow Anda, **star repo ini** agar lebih mudah ditemukan lagi. Masukan, kasus sintetis, dan kontribusi yang meningkatkan kualitas bukti sangat dihargai.

## Yang dibantu

| Pekerjaan | Hasil yang diharapkan dari agent |
| --- | --- |
| Pemetaan risiko | Alur aplikasi, data sensitif, siapa boleh mengakses apa, dan bagian yang belum diketahui |
| Review kode / perubahan | Alur input → validasi/izin → operasi → efek, lengkap dengan lokasi kode |
| Triase temuan | Pisahkan bukti di source, bukti uji lokal, dugaan yang perlu verifikasi, dan dugaan yang gugur |
| Perbaikan saat diminta | Patch root cause yang kecil, mempertahankan fungsi dan perubahan pengguna |
| Uji ulang | Tes regresi, kontrol pembanding, hasil aktual, dan pemeriksaan yang belum dilakukan |

Panduan mencakup autentikasi/sesi, akses objek/tenant/RLS, injection, XSS, file/upload, SSRF, rahasia, dependency, CI/konfigurasi, tool AI, dan logika bisnis. **Ini cakupan panduan review, bukan klaim semua area otomatis terdeteksi atau seluruh stack sudah diuji.** Agent menyesuaikan area dengan source, alat, dan izin yang tersedia.

Contoh: pengguna A bisa membaca catatan pengguna B. Agent tidak cukup melihat URL berisi ID; ia harus menelusuri middleware dan query, memeriksa aturan kepemilikan, lalu membedakan bukti source dari hasil uji dua identitas. Jika ternyata query sudah membatasi pemilik, dugaan harus gugur.

## Pasang skill saja

Folder yang dibutuhkan hanya [`skills/kodewaspada`](skills/kodewaspada). Python dan Semgrep **tidak diperlukan** untuk memakai skill. Baca instruksinya sebelum memasang.

Dari folder repo ini, pasang untuk satu proyek pada Linux/macOS/WSL; ganti `/path/ke/proyek-anda` dengan folder proyek Anda:

```bash
mkdir -p /path/ke/proyek-anda/.agents/skills
cp -R -i skills/kodewaspada /path/ke/proyek-anda/.agents/skills/
```

Jika folder `kodewaspada` sudah ada, jangan setujui overwrite sebelum membandingkan versi. Untuk instalasi personal, salin folder yang sama ke `~/.agents/skills/`. Instalasi personal membuat skill tersedia lintas proyek, bukan hanya repo ini. Struktur ini mengikuti format Agent Skills yang dipakai dalam [konsep Skills resmi OpenAI](https://developers.openai.com/plugins/concepts/skills). Jalur pemasangan dapat berbeda menurut host; jika skill belum muncul, mulai sesi baru atau restart aplikasi.

Di coding assistant lain yang dapat membaca file lokal, minta agent membaca `SKILL.md` beserta referensi yang ditunjuk. Integrasi native di luar Codex belum diuji; jangan menganggap nama folder/format agent setiap aplikasi sama.

## Tiga cara pakai

**Review dulu, tanpa mengubah aplikasi:**

```text
$kodewaspada Review folder aplikasi ini. Fokus pada login, akses data
antar pengguna, dan input ke database/HTML. Tunjukkan bukti dan batasnya.
```

**Perbaiki temuan yang sudah cukup terbukti:**

```text
$kodewaspada Perbaiki temuan akses data tadi pada kode lokal.
Pertahankan API dan perubahan saya. Tambahkan tes pemilik dan bukan pemilik.
```

**Periksa perbaikannya:**

```text
$kodewaspada Retest patch ini. Jalankan tes lokal yang relevan,
bandingkan akses yang sah dan yang harus ditolak, laporkan hasil sebenarnya.
```

Review tidak otomatis memberi izin edit, deploy, membuka PR, mempublikasikan laporan, atau menguji sistem produksi. Jika Anda sudah meminta fix, skill tidak meminta izin berulang untuk edit lokal yang memang termasuk tugas itu.

## Kenapa bukan hanya prompt "jadilah ahli security"?

Skill menetapkan cara mengambil keputusan: telusuri helper/middleware sampai operasi nyata, cari kontrol yang menggugurkan dugaan, jangan menganggap output scanner sebagai bukti, dan jangan menyebut retest lulus sebelum benar-benar dijalankan. Instruksi tersembunyi di komentar, log, atau file yang direview tidak boleh mengubah tugas agent.

Hasil yang diharapkan: **masalah → lokasi → bukti → dampak → perbaikan → retest**, ditambah area yang belum diperiksa. Tidak ada skor keamanan 0–100 atau label "100% aman".

## Scanner opsional

CLI Python yang sudah tersedia tetap bisa dipakai tanpa AI untuk tiga pemeriksaan taint JS/TS: input menuju shell, eval/Function, dan HTML mentah. Menghasilkan HTML, Markdown, dan JSON. Ini **alat bantu**, bukan prasyarat skill dan bukan seluruh cakupan review blue-team.

Instalasi engine, command, exit code, batas pemrosesan, dan privasi dijelaskan di [panduan scanner](docs/SCANNER.md). Jangan menjalankan contoh JavaScript di `examples/`; contoh tersebut hanya untuk analisis scanner.

## Privasi dan batas bukti

- Skill tidak memiliki backend. Namun source yang dibaca coding assistant dapat diproses provider AI host; gunakan lingkungan yang sesuai kebijakan proyek Anda.
- Jangan memasukkan credential, dump produksi, atau kode klien ke issue, contoh, atau laporan publik. Temuan secret ditulis dengan lokasi/jenis, bukan nilai rahasia.
- Provider AI, alat, konteks repo, dan izin memengaruhi hasil. Skill tidak memberikan akses Daybreak/TAC, tidak menjual akses tersebut, dan tidak memerlukan status program itu untuk review lokal.
- Analisis source, tes lokal, dan kondisi produksi adalah bukti yang berbeda. Tidak ada temuan bukan sertifikat aman; kegagalan alat harus disebutkan.

## Pengujian dan kontribusi

[Evaluasi perilaku](evals/README.md) memakai kasus sintetis dan penilaian hasil agent. [Catatan QA](docs/QA.md) membedakan evaluasi skill dari pengujian scanner. Mengubah teks skill perlu dievaluasi pada perilaku, bukan hanya validitas Markdown.

Laporkan dugaan kerentanan pada proyek ini melalui prosedur privat di [SECURITY.md](SECURITY.md); jangan membuka detail sensitif di issue publik.

```bash
python3 -m unittest discover -s tests -v
```

Tes scanner membutuhkan Semgrep untuk cakupan penuh; lihat panduannya. Perubahan aturan perlu contoh positif dan negatif. Perubahan skill perlu kasus yang memperlihatkan keputusan lebih baik, termasuk saat dugaan harus gugur. Jangan memakai data klien sebagai fixture.

## Lisensi nonkomersial dan berbagi

Instruksi, wrapper, aturan asli, contoh, dan dokumentasi KodeWaspada tersedia di bawah [PolyForm Noncommercial License 1.0.0](LICENSE) dengan `Required Notice: Copyright 2026 EL1Syum`. Ini lisensi **source-available**, bukan lisensi open-source OSI.

Anda boleh memakai, menyalin, mengubah, dan membagikan proyek untuk tujuan nonkomersial yang diizinkan lisensi. Saat membagikan salinan atau perubahan, sertakan ketentuan lisensi atau URL resminya dan pertahankan baris `Required Notice`. Menjual kembali, memasukkan KodeWaspada ke produk atau layanan berbayar, atau penggunaan komersial lain memerlukan lisensi tertulis terpisah dari pemegang hak. Ringkasan ini bukan pengganti teks lisensi.

Sebelum membuat rilis atau repo publik, ikuti [gerbang distribusi](docs/RELEASE.md). Riwayat pengembangan lokal sebelum `0.2.0` masih memuat lisensi lama dan tidak disiapkan untuk dipublikasikan.

Semgrep merupakan dependency terpisah dengan lisensi upstream sendiri, bukan engine yang dibundel dalam skill.
