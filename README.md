# Analisis Perbandingan Welsh–Powell dan DSATUR untuk Penjadwalan Mata Kuliah Berbasis Pewarnaan Graf

Repositori ini memuat implementasi, eksperimen, data, dan naskah IEEE untuk
perbandingan berpasangan dua heuristik pewarnaan graf pada persoalan
penjadwalan mata kuliah.

- **Naskah:** `paper/main.pdf` (8 halaman, IEEE conference, A4, dua kolom)
- **Beban kerja:** 690 instans graf sintetis, 690 perbandingan langsung,
  1.380 eksekusi algoritma utama, ditambah satu studi kasus nyata
- **Verifikasi eksak:** bilangan kromatik terbukti pada 447 instans (64.8% benchmark)
- **Status validasi:** 267 uji otomatis lulus, Ruff bersih, 76 klaim numerik
  naskah diperiksa terhadap snapshot hasil yang dibekukan

## Ringkasan hasil terukur

| Besaran | Nilai |
|---|---|
| Rata-rata warna Welsh–Powell | 11.89 |
| Rata-rata warna DSATUR | 11.10 |
| Reduksi rata-rata $R_k$ | 7.17% |
| Menang / seri / kalah (DSATUR) | 390 / 285 / 15 dari 690 |
| Uji Wilcoxon jumlah warna | $p = 4.2\times10^{-66}$, $r = -0.95$ |
| Rasio waktu DSATUR : Welsh–Powell | 3.09 |
| Celah optimalitas rata-rata (447 instans terbukti) | WP 15.75%, DSATUR 7.06% |
| DSATUR mencapai $\chi(G)$ | 61.3% instans |
| Graf nyata (156 mata kuliah, 975 mahasiswa) | $\chi(G)=13$ terbukti, kedua heuristik optimal |
| Konflik pewarnaan pada seluruh keluaran | 0 |

Temuan utama bersifat bersyarat: keunggulan DSATUR menyusut dari 11.14% pada
$p=0.1$ menjadi 5.49% pada $p=0.7$, dan praktis hilang pada graf pendaftaran
terstruktur (83 dari 90 instans seri).

## Struktur proyek

```text
.
├── paper/
│   ├── main.tex              # naskah IEEEtran (Bahasa Indonesia)
│   ├── references.bib        # 18 rujukan, metadata terverifikasi
│   ├── main.pdf              # hasil kompilasi
│   ├── figures/              # gambar PDF vektor + pratinjau PNG
│   └── tables/               # tabel LaTeX yang dihasilkan otomatis
├── src/
│   ├── graph_model.py        # representasi graf dan validasi pewarnaan
│   ├── welsh_powell.py       # Welsh–Powell (greedy + versi pemindaian kelas)
│   ├── dsatur.py             # DSATUR greedy (heap + acuan O(n^2+m))
│   ├── exact_coloring.py     # bilangan kromatik eksak (branch and bound)
│   ├── graph_generator.py    # generator Erdős–Rényi G(n,p)
│   ├── enrollment_generator.py  # simulasi pendaftaran mata kuliah
│   ├── real_dataset.py       # pemuat data pendaftaran nyata (SHA-256 dipin)
│   ├── graph_audit.py        # audit struktur seluruh instans
│   ├── illustrative_example.py  # contoh kerja 7 mata kuliah / 5 mahasiswa
│   ├── benchmark.py          # driver eksperimen berpasangan
│   ├── optimality_study.py   # celah optimalitas pada instans terbukti
│   ├── real_case_study.py    # studi kasus graf nyata
│   ├── analysis.py           # Wilcoxon, bootstrap, Holm, ukuran efek
│   ├── make_tables.py        # tabel LaTeX + key_numbers.json
│   ├── visualization.py      # gambar publikasi
│   ├── freeze_results.py     # snapshot hasil + manifest SHA-256
│   └── verify_claims.py      # pemeriksa angka naskah vs snapshot
├── tests/                    # 267 uji pytest
├── data/
│   ├── instances_metadata.csv
│   └── external/             # data pendaftaran nyata (CC BY 4.0)
├── results/
│   ├── raw_results.csv, statistics.json, optimality.*, graph_audit.*, ...
│   └── frozen/v1/            # snapshot kanonis + FROZEN_MANIFEST.json
├── requirements.txt
├── pyproject.toml
├── run_all.py
└── presentation/
    └── naskah_presentasi.md   # naskah presentasi 12 slide + Q&A
```

## Kebutuhan

- Python 3.11 atau lebih baru (diuji pada 3.13.15)
- Pustaka pada `requirements.txt`
- Untuk kompilasi naskah: distribusi TeX dengan `IEEEtran.cls`, `amsmath`,
  `booktabs`, `algorithm`, `algpseudocode` (diuji dengan MiKTeX 25.12)

```bash
python -m pip install -r requirements.txt
```

## Data pendaftaran nyata

Eksperimen C memakai arsip **Dataset for ETP** (P. C. Le, Zenodo, 2025,
`doi:10.5281/zenodo.17129990`, lisensi CC BY 4.0). Unduh
`StudentSubjectUnique.csv` ke `data/external/`:

```bash
curl -L -o data/external/StudentSubjectUnique.csv \
  https://zenodo.org/api/records/17129990/files/StudentSubjectUnique.csv/content
```

Berkas diverifikasi terhadap SHA-256 yang dipin di `src/real_dataset.py`
(`b1833dc0…`); pemuat menolak berkas yang berbeda. Hanya matriks kehadiran
mahasiswa–mata kuliah yang dibaca — tidak ada nama, nilai, atau atribut pribadi.
Uji yang bergantung pada data ini dilewati otomatis bila berkas tidak ada.

**Pencarian dataset kedua.** Kandidat lain diperiksa dan ditolak dengan alasan
yang dapat diverifikasi: arsip Cornell (arXiv:2409.04959) tidak menyatakan
lisensi apa pun; arsip MUJ (Zenodo 23093611/23093609) berlisensi CC BY 4.0
tetapi masih embargo; dan *Complete Examination Dataset* (Zenodo 18324561,
CC BY 4.0) hanya memuat jadwal ujian yang sudah tersusun, bukan data pendaftaran,
sehingga tidak dapat dipakai untuk membentuk graf konflik. Karena itu studi ini
memakai satu instans nyata, dan batas validitas eksternalnya dinyatakan terbuka
di naskah.

## Reproduksi lengkap

```bash
python run_all.py
```

Perintah tersebut menjalankan, berurutan: uji unit, Ruff, benchmark 690 instans,
audit struktur, studi optimalitas eksak, studi kasus nyata, pembuatan tabel,
pembuatan gambar, dan verifikasi klaim terhadap snapshot yang dibekukan.

Untuk menjalankan tahap tertentu saja:

```bash
python -m pytest                                   # 267 uji
python -m ruff check src tests                     # lint
python src/benchmark.py --repeats 7                # eksperimen penuh (~20-40 s)
python src/graph_audit.py                          # audit struktur
python src/optimality_study.py                     # celah optimalitas eksak
python src/real_case_study.py                      # studi kasus nyata
python src/make_tables.py                          # tabel + key_numbers.json
python src/visualization.py                        # gambar ke paper/figures
python src/freeze_results.py --version v1 --force  # bekukan snapshot
python src/verify_claims.py                        # cek angka naskah
```

> **Catatan tentang waktu eksekusi.** Waktu tidak dapat direproduksi persis.
> Menjalankan ulang benchmark atau studi kasus nyata akan mengubah nilai
> milidetik dan beberapa angka pada naskah. `src/verify_claims.py` memeriksa
> naskah terhadap `results/frozen/v1/`, bukan terhadap pengukuran baru, dan akan
> menandai setiap ketidakcocokan. Setelah memperbarui naskah, bekukan snapshot
> baru (`--version v2`) alih-alih menimpa yang lama.

## Kompilasi naskah

`latexmk` memerlukan Perl; bila tidak tersedia, gunakan urutan `pdflatex`
berikut dari dalam direktori `paper/`:

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Hasilnya `paper/main.pdf`, 8 halaman A4 dua kolom.

## Rancangan eksperimen

**Eksperimen A — graf acak.** Model Erdős–Rényi $G(n,p)$ dengan
$|V| \in \{20,40,60,80,100\}$, $p \in \{0.1,0.3,0.5,0.7\}$, dan 30 ulangan per
sel, sehingga 600 instans. Setiap pasangan simpul diundi dari satu aliran
seragam NumPy PCG64; benih diturunkan deterministik dari $(|V|, p, \text{ulangan})$.

**Eksperimen B — simulasi pendaftaran.** Tabel pendaftaran disimulasikan lebih
dahulu (bobot popularitas Dirichlet, jendela semester, beban studi acak), lalu
graf diturunkan dari pendaftaran bersama. Tiga skenario × 30 benih = 90 instans.
Seluruh data bersifat sintetis, bukan catatan universitas.

**Eksperimen C — graf nyata.** Satu graf dari data pendaftaran teranonimisasi
(156 mata kuliah, 975 mahasiswa, 1.029 sisi). Dilaporkan secara deskriptif,
bukan sebagai uji hipotesis.

**Audit struktur.** Setiap instans diukur kepadatan, derajat, jumlah komponen,
koefisien klaster, dan batas bawah klik. Hasilnya memisahkan dua rezim: pada
graf Erdős–Rényi koefisien klaster ≈ $p$ (rata-rata 0.397), sedangkan pada graf
pendaftaran jauh lebih tinggi (0.776 sintetis, 0.649 nyata).

**Verifikasi eksak.** Pencarian *branch-and-bound* berurut DSATUR menghitung
$\chi(G)$ pada sel yang dapat diselesaikan dalam batas 60 detik: Eksperimen A
dengan $|V|\in\{20,40\}$ (semua $p$), $|V|=60$ untuk $p\le 0.5$, $|V|=80$ untuk
$p=0.1$, serta seluruh Eksperimen B. Dari 450 instans yang dicoba, 447 terbukti
(99.3%), yaitu 64.8% dari seluruh benchmark; 3 dilaporkan sebagai tidak terbukti,
bukan sebagai optimum. Pencari divalidasi terhadap keluarga graf yang diketahui
dan terhadap pencarian menyeluruh pada 120 graf acak kecil. Studi penuh memakan
waktu sekitar 10 menit; `--quick` membatasi ke $|V|\le 40$.

**Protokol waktu.** `time.perf_counter` (monoton, nanodetik), tujuh pengulangan
per algoritma per instans, ringkasan median, kedua algoritma dijalankan
bergantian, pembangkitan graf diukur terpisah, dan satu instans pemanasan
dijalankan sebelum pengukuran.

**Analisis statistik.** Rancangan berpasangan. Dua luaran ditetapkan sebagai uji
primer (jumlah warna dan waktu pada seluruh 690 instans); uji peringkat bertanda
Wilcoxon dua sisi, $\alpha = 0.05$, korelasi peringkat-biserial, dan selang
kepercayaan bootstrap persentil 95% (10.000 resampel, benih tetap). Seluruh
analisis subkelompok bersifat eksploratif dan dikoreksi Holm di dalam
keluarganya. Satuan analisis adalah instans, bukan pengulangan waktu.

## Integritas dan batasan

- Tidak ada angka kinerja yang dikarang: seluruh tabel dan gambar dihasilkan
  dari `results/`, dan `src/verify_claims.py` memeriksa ulang setiap angka yang
  dikutip naskah terhadap snapshot `results/frozen/v1/`.
- Tidak ada rujukan yang dikarang: metadata 18 entri `references.bib`
  diverifikasi melalui Crossref API (kecuali Erdős–Rényi 1960 yang tidak
  memiliki DOI, dan dataset Zenodo yang DOI-nya terdaftar).
- Kedua algoritma adalah heuristik. Celah optimalitas hanya dilaporkan untuk
  instans yang $\chi(G)$-nya terbukti; untuk instans lain hanya batas
  $\omega(G)\le\chi(G)\le\min(k_{\mathrm{WP}},k_{\mathrm{DS}})$ yang berlaku.
- Model hanya memuat kendala konflik mata kuliah. Ketersediaan dosen, kapasitas
  ruang, durasi, dan preferensi waktu tidak dimodelkan. Dataset nyata tidak
  memuat penugasan dosen, sehingga sisi konflik dosen tidak dibentuk dan tidak
  dilengkapi dengan informasi yang dikarang.
- Bukti nyata terbatas pada satu institusi dan satu potret pendaftaran ujian;
  generalisasi ke institusi lain masih memerlukan data konflik dari institusi
  tersebut.
- Waktu absolut maupun rasio bergantung pada mesin uji (Windows 11 ARM64,
  Qualcomm Snapdragon, 8 inti logis), bahasa pemrograman, dan detail
  implementasi. Yang lebih dapat digeneralisasi adalah pola pertumbuhan
  asimtotiknya, bukan nilai milidetik maupun faktor percepatan.

## Metadata penulis

Blok `\author` di `paper/main.tex` memuat metadata penulis tunggal:

- **Nama:** Muhammad Akbar Yurizal Saputra
- **Program studi:** Teknik Informatika
- **Fakultas:** Fakultas Matematika dan IPA
- **Institusi:** Universitas Negeri Semarang
- **Lokasi:** Semarang, Indonesia
- **Surel:** akbaryurizal@students.unnes.ac.id

Tidak ada nomor keanggotaan IEEE, ORCID, atau afiliasi tambahan.
