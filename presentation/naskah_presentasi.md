# Naskah Presentasi — Welsh–Powell vs DSATUR untuk Penjadwalan Mata Kuliah

**Penulis:** Muhammad Akbar Yurizal Saputra — Teknik Informatika, Fakultas Matematika dan IPA, Universitas Negeri Semarang

**Judul paper:** *Analisis Perbandingan Algoritma Welsh–Powell dan DSATUR untuk Penjadwalan Mata Kuliah Berbasis Pewarnaan Graf*

**Durasi:** ±13 menit presentasi + 3–5 menit tanya jawab (12 slide)

**Cara pakai:** setiap slide berisi (a) poin yang ditampilkan di layar, (b) naskah yang dibacakan, dan (c) petunjuk visual. Naskah ditulis dalam Bahasa Indonesia akademik yang natural untuk dibicarakan, bukan dibaca kaku.

---

## Slide 1 — Judul (0:30)

**Di layar:**
> Analisis Perbandingan Algoritma Welsh–Powell dan DSATUR untuk Penjadwalan Mata Kuliah Berbasis Pewarnaan Graf
>
> Muhammad Akbar Yurizal Saputra
> Teknik Informatika — Fakultas Matematika dan IPA
> Universitas Negeri Semarang

**Naskah:**
"Selamat pagi/siang, Bapak Ibu. Saya Muhammad Akbar Yurizal Saputra dari Universitas Negeri Semarang. Hari ini saya akan mempresentasikan hasil penelitian saya yang membandingkan dua algoritma pewarnaan graf klasik — Welsh–Powell dan DSATUR — ketika diterapkan pada masalah penjadwalan mata kuliah."

**Visual:** judul paper, nama, afiliasi. Bisa menampilkan Gambar 1 paper (contoh graf konflik 7 mata kuliah) sebagai latar kecil.

---

## Slide 2 — Latar Belakang (1:00)

**Di layar:**
- Penjadwalan = menempatkan mata kuliah ke slot waktu tanpa tabrakan
- Mata kuliah → simpul; mahasiswa yang sama → sisi konflik
- Jumlah slot minimum = bilangan kromatik χ(G) → **NP-hard**
- Praktiknya bergantung pada **heuristik**

**Naskah:**
"Persoalan penjadwalan mata kuliah bisa kita terjemahkan ke dalam bahasa graf. Setiap mata kuliah menjadi sebuah simpul. Dua mata kuliah yang diambil oleh mahasiswa yang sama tidak boleh berada di slot waktu yang sama, sehingga kita hubungkan dengan sebuah sisi. Dengan demikian, mencari jumlah slot paling sedikit sama dengan mencari bilangan kromatik graf konflik. Sayangnya, menentukan bilangan kromatik merupakan masalah NP-hard. Karena itu, dalam praktiknya kita memakai heuristik — algoritma yang cepat dan selalu menghasilkan pewarnaan yang sah, tetapi tanpa jaminan optimal."

**Visual:** diagram sederhana: 3 mata kuliah dengan sisi, lalu 3 warna.

---

## Slide 3 — Pertanyaan Penelitian & Kontribusi (1:00)

**Di layar:**
- **RQ1** Algoritma mana yang lebih sedikit warnanya?
- **RQ2** Bagaimana pengaruh kepadatan graf?
- **RQ3** Bagaimana pengaruh ukuran & kepadatan terhadap waktu?
- **RQ4** Pada kondisi apa masing-masing unggul atau seri?
- Kontribusi: eksperimen berpasangan + verifikasi eksak + studi kasus nyata

**Naskah:**
"Penelitian ini menjawab empat pertanyaan. Pertama, mana yang lebih hemat warna. Kedua, bagaimana kepadatan graf mengubah jumlah warna. Ketiga, bagaimana ukuran dan kepadatan memengaruhi waktu eksekusi. Keempat, pada kondisi graf seperti apa masing-masing algoritma unggul, kalah, atau seri. Kontribusinya ada tiga: eksperimen berpasangan yang reproducible, verifikasi bilangan kromatik secara eksak pada subhimpunan instans, dan satu studi kasus memakai data pendaftaran nyata."

**Visual:** empat kotak RQ.

---

## Slide 4 — Model Penjadwalan (1:00)

**Di layar:**
- Graf konflik: $G=(V,E)$
- Sisi dari pendaftaran bersama: $E=\{\{u,v\}: S_u\cap S_v\neq\varnothing\}$
- Pewarnaan sah: $c(u)\neq c(v)$ untuk setiap $\{u,v\}\in E$
- Tujuan: $\min k$
- Kepadatan: $d(G)=2|E|/(|V|(|V|-1))$

**Naskah:**
"Modelnya sederhana dan sengaja disederhanakan. Graf konflik didefinisikan sebagai pasangan simpul dan sisi. Sebuah sisi ada jika dua mata kuliah memiliki setidaknya satu mahasiswa yang sama. Pewarnaan dikatakan sah jika setiap pasangan bertetangga menerima warna berbeda. Tujuannya meminimumkan jumlah warna. Kepadatan graf dihitung dengan rumus standar, dan kami selalu membedakan antara probabilitas pembangkitan p dan kepadatan yang benar-benar teramati. Kami juga ingin menekankan: model ini hanya menangkap konflik mahasiswa. Dosen, ruang, durasi, dan preferensi waktu tidak dimasukkan."

**Visual:** persamaan (1), (2), (3), (6), (7) dari paper.

---

## Slide 5 — Dua Algoritma (1:30)

**Di layar:**

| | Welsh–Powell | DSATUR greedy |
|---|---|---|
| Urutan | derajat menurun, seri → id | saturasi terbesar, seri → derajat → id |
| Warna | terkecil yang tersedia | terkecil yang tersedia |
| Kompleksitas | $O(n+m)$ | $O((n+m)\log n)$ |

**Naskah:**
"Welsh–Powell mengurutkan simpul berdasarkan derajat menurun, lalu mewarnai secara greedy dengan warna terkecil yang belum dipakai tetangganya. Karena urutannya deterministik, hasilnya selalu sama. DSATUR mengambil pendekatan adaptif: pada setiap langkah ia memilih simpul belum berwarna dengan derajat saturasi terbesar — yaitu jumlah warna berbeda pada tetangga yang sudah berwarna. Jika seri, dipakai derajat, lalu nomor simpul. Secara kompleksitas, Welsh–Powell linear, sementara DSATUR memakai heap sehingga menjadi O((n+m) log n). Perlu dicatat, yang kami uji adalah versi greedy DSATUR, bukan versi eksak branch-and-bound."

**Visual:** pseudocode Algoritma 1 dan 2 dari paper, atau tabel ringkas di atas.

---

## Slide 6 — Metodologi Eksperimen (1:30)

**Di layar:**
- **A:** 600 graf Erdős–Rényi — $|V|\in\{20,40,60,80,100\}$, $p\in\{0.1,0.3,0.5,0.7\}$, 30 ulangan/sel
- **B:** 90 graf dari simulasi pendaftaran (3 skenario × 30 benih)
- **C:** 1 graf pendaftaran nyata (Zenodo CC BY 4.0, 975 mahasiswa, 156 mata kuliah)
- 690 instans sintetis → **690 perbandingan berpasangan** → **1.380 eksekusi algoritma utama**
- 7 pengukuran waktu/instans, median; pembangkitan graf diukur terpisah

**Naskah:**
"Eksperimen A memakai 600 graf acak Erdős–Rényi: lima ukuran, empat nilai probabilitas sisi, tiga puluh ulangan per sel. Eksperimen B membangkitkan 90 graf dari simulasi pendaftaran mahasiswa — tiga skenario program studi, masing-masing tiga puluh benih. Di luar itu, saya menganalisis satu graf pendaftaran nyata yang dianonimkan sebagai studi kasus terpisah. Jadi totalnya 690 instans sintetis, menghasilkan 690 perbandingan langsung dan 1.380 eksekusi algoritma utama. Tujuh kali pengukuran waktu per instans diringkas menjadi median, dan waktu pembangkitan graf tidak ikut dihitung."

**Visual:** tabel komposisi data (Tabel I paper).

---

## Slide 7 — Validasi & Statistik (0:45) *(opsional, bisa digabung ke slide 6)*

**Di layar:**
- 268 uji otomatis lulus; 0 konflik pewarnaan
- Wilcoxon dua sisi, $\alpha=0{,}05$; efek $r$; bootstrap 10.000 resampel
- Uji primer: warna & waktu. Subkelompok: eksploratif, Holm
- Snapshot hasil dibekukan: `results/frozen/v2` (77 klaim tervalidasi)

**Naskah:**
"Sebelum eksperimen, saya menjalankan 268 uji otomatis, termasuk uji determinisme dan kesetaraan implementasi. Seluruh keluaran terverifikasi memiliki nol konflik pewarnaan. Untuk analisis, dua luaran ditetapkan sebagai uji primer — jumlah warna dan waktu — memakai uji Wilcoxon berpasangan. Analisis per subkelompok bersifat eksploratif dan sudah dikoreksi Holm. Seluruh angka dalam makalah dibekukan dalam snapshot v2 dan diverifikasi oleh 77 klaim numerik."

---

## Slide 8 — Hasil RQ1 & RQ2 (1:30)

**Di layar:**
- DSATUR **11,10** warna vs Welsh–Powell **11,89** warna
- Reduksi rata-rata **7,17%**; $p=4{,}2\times10^{-66}$, $r=-0{,}95$
- Menang / seri / kalah = **390 / 285 / 15**
- Keunggulan menyusut: **11,14%** ($p=0{,}1$) → **5,49%** ($p=0{,}7$)

**Naskah:**
"Hasil utama: DSATUR rata-rata memakai 11,10 warna, sementara Welsh–Powell 11,89. Reduksinya 7,17 persen, dan secara statistik sangat kuat — nilai p dalam orde 10⁻⁶⁶ dengan ukuran efek hampir sempurna. Namun keunggulan ini tidak universal. Dari 690 instans, DSATUR menang 390 kali, seri 285 kali, dan kalah 15 kali. Menariknya, keunggulannya menyusut ketika graf makin padat: dari 11,14 persen pada p sama dengan 0,1 menjadi 5,49 persen pada p sama dengan 0,7."

**Catatan angka penting:** 15 kemenangan Welsh–Powell terkonsentrasi pada graf kecil–sedang dengan kepadatan menengah–tinggi; 10 dari 13 kemenangan di Eksperimen A terjadi pada $|V|\le40$.

**Visual:** Gambar 1 paper (panel atas: rata-rata warna per ukuran dan $p$).

---

## Slide 9 — Hasil RQ3 & RQ4 (1:30)

**Di layar:**
- DSATUR **3,09× lebih lambat** (kisaran 2,92–3,13)
- $p=1{,}2\times10^{-114}$, $r=1{,}00$ — lebih lambat pada **setiap** pasangan
- Graf pendaftaran terstruktur: **83 dari 90 seri**; reduksi 0,00–0,48%
- Rasio waktu bersifat **spesifik mesin & implementasi**

**Naskah:**
"Biaya yang dibayar DSATUR adalah waktu. Secara agregat ia sekitar 3,09 kali lebih lambat, dan uji Wilcoxon menunjukkan DSATUR lebih lambat pada setiap pasangan instans. Namun angka absolut maupun rasionya sangat bergantung pada mesin dan detail implementasi; yang bisa digeneralisasi adalah pola pertumbuhannya. Untuk RQ4, temuan pentingnya: pada graf pendaftaran yang terstruktur, 83 dari 90 instans berakhir seri. Jadi klaim bahwa DSATUR selalu lebih baik tidak didukung data kami."

**Visual:** Gambar 1 paper (panel bawah: waktu median, skala log).

---

## Slide 10 — Verifikasi Optimalitas Eksak (1:30)

**Di layar:**
- Pencarian branch-and-bound berurut DSATUR; batas atas = min(solusi WP, DSATUR)
- **447 dari 450** instans yang dicoba terbukti (**99,3%**), = **64,8%** dari 690
- Celah rata-rata: WP **15,75%**, DSATUR **7,06%**
- DSATUR mencapai χ(G) pada **61,3%**, WP pada **38,7%**
- Untuk 243 instans sisanya: hanya batas $\omega(G)\le\chi(G)\le\min(k_{WP},k_{DS})$

**Naskah:**
"Untuk mengukur seberapa jauh kedua heuristik dari optimum, saya menjalankan pencarian eksak branch-and-bound. Dari 450 instans yang dicoba, 447 berhasil dibuktikan bilangan kromatiknya — 99,3 persen, atau sekitar 65 persen dari seluruh benchmark. Celah rata-rata Welsh–Powell 15,75 persen dan DSATUR 7,06 persen. DSATUR mencapai optimum pada 61,3 persen instans. Pada 243 instans yang belum terbukti, kami tidak mengklaim apa pun selain batas matematis yang valid. Ini adalah batas komputasi, bukan kesimpulan tentang kualitas algoritma."

**Visual:** Tabel V paper (matriks celah optimalitas).

---

## Slide 11 — Studi Kasus Graf Nyata (1:00)

**Di layar:**
- 156 mata kuliah, 975 mahasiswa, 1.029 sisi, kepadatan 0,085
- Koefisien klaster **0,649** (vs 0,397 acak; 0,776 sintetis)
- $\chi(G)=13$ **terbukti** — klik berukuran 13 dan pewarnaan 13 warna
- WP = DSATUR = **13 warna**; DSATUR 3,75× lebih lambat

**Naskah:**
"Sebagai uji validitas eksternal, saya memakai data pendaftaran ujian teranonimisasi dari arsip Zenodo berlisensi CC BY 4.0. Grafnya memiliki 156 mata kuliah dan 1.029 sisi. Yang menarik, koefisien klasternya 0,649 — jauh lebih tinggi daripada graf acak, dan menempatkannya di antara dua keluarga sintetis kami. Bilangan kromatiknya terbukti 13, karena ada klik berukuran 13 sekaligus pewarnaan sah dengan 13 warna. Kedua heuristik mencapai nilai itu, sehingga keduanya optimal pada instans ini — dan DSATUR tetap lebih lambat."

**Visual:** tabel ringkas hasil studi kasus.

---

## Slide 12 — Kesimpulan & Penutup (1:00)

**Di layar:**
- DSATUR lebih hemat warna pada graf acak renggang & besar, tetapi lebih lambat
- Pada graf terstruktur, keduanya hampir selalu setara dan sering optimal
- Pilihan algoritma bersifat **kondisional**, bukan mutlak
- Keterbatasan: model disederhanakan, satu institusi, 243 instans tanpa bukti optimum

**Naskah:**
"Kesimpulannya bersifat bersyarat. DSATUR lebih tepat jika prioritasnya adalah menekan jumlah slot dan graf konflik cenderung renggang serta besar. Welsh–Powell lebih tepat ketika waktu komputasi, kesederhanaan, atau ukuran graf kecil menjadi pertimbangan. Pada graf terstruktur keduanya hampir selalu setara. Saya sengaja tidak menyatakan bahwa salah satu algoritma selalu menang. Keterbatasannya juga saya sampaikan dengan terbuka: model hanya memuat konflik mahasiswa, data nyata berasal dari satu institusi, dan 243 instans masih belum memiliki bukti optimum. Terima kasih atas perhatiannya. Saya siap menerima pertanyaan."

**Visual:** ringkasan 3 poin + "Terima Kasih" + kontak: akbaryurizal@students.unnes.ac.id.

---

## Lampiran A — Persiapan Tanya Jawab

**Q1. Mengapa DSATUR lebih lambat padahal lebih sedikit warnanya?**
Karena DSATUR memelihara derajat saturasi dan memakai heap. Setiap pewarnaan memperbarui tetangga dan mungkin mendorong entri baru ke heap. Kompleksitasnya O((n+m) log n) versus O(n+m) untuk Welsh–Powell. Dalam implementasi ini, rasio yang teramati 3,09 kali, tetapi itu spesifik mesin dan implementasi.

**Q2. Apakah ini sudah jadwal universitas yang siap pakai?**
Belum. Model ini hanya menghasilkan jumlah slot minimum untuk konflik mahasiswa. Ketersediaan dosen, kapasitas ruang, durasi kuliah, dan preferensi waktu tidak dimodelkan.

**Q3. Mengapa tidak semua instans dibuktikan optmumnya?**
Karena keterbatasan komputasi. Pencarian eksak menjadi mahal pada graf besar dan padat. Dari 450 yang dicoba, 447 terbukti; sisanya berhenti pada batas simpul. Untuk itu kami hanya melaporkan batas $\omega(G)\le\chi(G)\le\min(k_{WP},k_{DS})$, bukan celah.

**Q4. Apakah DSATUR selalu lebih baik?**
Tidak. Ada 15 instans tempat Welsh–Powell menang, 285 seri, dan pada 90 graf pendaftaran sintetis 83 di antaranya seri. Pada studi kasus nyata keduanya sama-sama optimal. Jadi klaim "selalu lebih baik" tidak didukung data.

**Q5. Dari mana data nyatanya dan apakah aman secara etika?**
Dari arsip *Dataset for ETP* (Zenodo, DOI 10.5281/zenodo.17129990, CC BY 4.0). Identifier mahasiswa sudah dianonimisasi; saya hanya membaca matriks kehadiran mahasiswa–mata kuliah, bukan nama, nilai, atau atribut pribadi. Berkas diverifikasi dengan SHA-256.

**Q6. Apakah perbedaan ini signifikan secara statistik?**
Ya, untuk luaran primer. Uji Wilcoxon berpasangan memberi $p=4{,}2\times10^{-66}$ untuk jumlah warna dan $p=1{,}2\times10^{-114}$ untuk waktu, dengan ukuran efek $r=-0{,}95$ dan $r=1{,}00$. Analisis subkelompok bersifat eksploratif dan sudah dikoreksi Holm.

**Q7. Bagaimana reproduksibilitasnya?**
Benih acak tercatat,snapshot hasil dibekukan di `results/frozen/v2` dengan manifest SHA-256, dan 77 klaim numerik diverifikasi otomatis terhadap snapshot itu. Kode dan data ada di repositori GitHub privat saya.

---

## Lampiran B — Versi Ringkas 5 Menit

1. **Judul** (0:15) — nama, afiliasi, judul.
2. **Masalah** (0:45) — penjadwalan → pewarnaan graf; χ(G) NP-hard.
3. **Metode** (1:00) — 690 instans sintetis + 1 kasus nyata; WP vs DSATUR; 1.380 eksekusi.
4. **Hasil utama** (1:30) — DSATUR 11,10 vs WP 11,89; reduksi 7,17%; menang/seri/kalah 390/285/15; tapi 3,09× lebih lambat.
5. **Optimalitas & kasus nyata** (1:00) — 447 terbukti; celah 7,06% vs 15,75%; graf nyata χ=13, keduanya optimal.
6. **Kesimpulan** (0:30) — pilihan bersifat kondisional; keterbatasan model; terima kasih.

---

## Lampiran C — Daftar Angka Kunci (untuk dicek sebelum presentasi)

| Besaran | Nilai |
|---|---|
| Instans sintetis | 690 (600 acak + 90 pendaftaran) |
| Perbandingan berpasangan | 690 |
| Eksekusi algoritma utama | 1.380 |
| Studi kasus nyata | 1 (156 mata kuliah, 975 mahasiswa) |
| Rata-rata warna WP / DSATUR | 11,89 / 11,10 |
| Reduksi warna | 7,17% |
| p-value (warna) | $4{,}2\times10^{-66}$ |
| Efek $r$ (warna) | $-0{,}95$ |
| Menang/seri/kalah | 390 / 285 / 15 |
| Rasio waktu DSATUR/WP | 3,09 (2,92–3,13) |
| Reduksi $p=0{,}1\to p=0{,}7$ | 11,14% → 5,49% |
| Seri pada graf pendaftaran | 83 dari 90 |
| Instans dengan χ terbukti | 447 dari 450 yang dicoba (64,8% dari 690) |
| Celah WP / DSATUR | 15,75% / 7,06% |
| DSATUR mencapai χ | 61,3% |
| Graf nyata | χ=13, kedua heuristik optimal, DSATUR 3,75× lebih lambat |
| Uji otomatis | 268 lulus |
| Klaim terverifikasi | 77 (snapshot v2) |
| Struktur paper | 8 halaman, 18 referensi, 14 persamaan, 5 tabel, 1 gambar |
