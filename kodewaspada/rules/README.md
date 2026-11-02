# Batas tiga aturan awal

Aturan ini ditulis untuk KodeWaspada, bukan disalin dari Semgrep Registry.
Pengujian memakai **Semgrep CE 1.179.0**, diverifikasi lokal pada **2 November
2026**. Ini teknik analisis taint yang sudah mapan, bukan teknik baru/zero-day.

| ID | Sumber yang dikenali | Tujuan berisiko yang dikenali |
| --- | --- | --- |
| KW001 / `kw-request-shell` | `query`, `body`, `params` dari parameter pertama fungsi bernama `req` atau `request` | `exec`/`execSync` yang diimpor dari `child_process` atau `node:child_process`; ESM dan bentuk `require` yang diuji |
| KW002 / `kw-request-eval` | Sumber request di atas serta `location.search/hash/href`, `window.location`, `document.location` | `eval`, body terakhir `new Function`/`Function` |
| KW003 / `kw-request-html` | Sumber request dan lokasi browser di atas | Nilai `innerHTML`, JSX `dangerouslySetInnerHTML`, argumen `res.send`/`response.send` |

Nama `req`/`request` adalah **konvensi**, bukan bukti bahwa pemanggil menerima
HTTP atau nilai dikuasai penyerang. Pembayangan global browser, fungsi pembungkus,
validasi custom, dan alur lintas fungsi/file perlu diperiksa manusia. Sumber yang
tidak dimodelkan bisa terlewat. `res.send` dapat menghasilkan JSON atau teks
biasa: hasilnya tetap kandidat keluaran HTML, **bukan XSS terkonfirmasi**.

Untuk KW003, sanitizer hanya dikenali sebagai pemanggilan satu argumen
`sanitize` dari default import `dompurify`. Aturan tidak menyembunyikan
pemanggilan dengan parameter konfigurasi, binding yang dibayangi parameter
fungsi, atau konfigurasi/hook/mutasi langsung yang terlihat. Pengaturan dari
file lain, versi DOMPurify yang rentan, dan perubahan lewat alias belum
diverifikasi. Nama `sanitize` saja tidak dipercaya. Tidak ada sanitizer HTML/URL
yang dianggap melindungi shell atau evaluator JavaScript.

## Bukti implementasi dan sumber primer

Semua sumber berikut dibuka pada **2 November 2026**. Tanggal pembaruan yang
tidak tampil ditulis demikian, bukan dianggap terbaru.

| Keputusan | Sumber dan tanggal/versi terlihat | Penerapan |
| --- | --- | --- |
| Taint lokal dan exact source/sanitizer | [Semgrep taint overview](https://docs.semgrep.dev/writing-rules/data-flow/taint-mode/overview); tanggal halaman tidak tercantum; runtime 1.179.0 diuji | Gunakan `mode: taint`, `exact: true`, dan kontrol positif/negatif, tanpa menjanjikan analisis lintas fungsi Pro |
| Cocokkan AST/import, bukan regex isi file | [Semgrep pattern syntax](https://docs.semgrep.dev/writing-rules/pattern-syntax); tanggal halaman tidak tercantum | Ikat impor proses anak dan gunakan regex hanya untuk membatasi nama binding/module yang cocok |
| Shell berbeda dari array argumen | [Node child_process](https://nodejs.org/api/child_process.html); halaman v26.13.0; tanggal publikasi tidak tercantum | Tinjau `exec`/`execSync`; jelaskan `execFile` tanpa shell tidak otomatis meniadakan penyalahgunaan argumen |
| `innerHTML` mem-parsing HTML | [MDN innerHTML](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML); diperbarui 12 Oktober 2026 | Utamakan `textContent` untuk teks, labeli kandidat bukan bukti XSS |
| Sanitizer tergantung konteks | [DOMPurify maintainer README](https://github.com/cure53/DOMPurify); README menampilkan v3.4.17, tanggal perubahan bagian tidak tercantum | Hanya suppress bentuk import/pemanggilan sempit; tidak memverifikasi versi DOMPurify pada proyek pengguna |

Uji yang dapat diulang dari root repo:

```bash
python3 -m unittest discover -s tests -p test_rules.py -v
```

Fixture hanya dibaca, tidak dieksekusi. Pengujian ini membuktikan perilaku pada
contoh yang tersedia, bukan tingkat akurasi umum pada semua proyek JavaScript.
