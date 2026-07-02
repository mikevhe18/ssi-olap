# ssi_olap_dashboard_builder

Modul Odoo 14 untuk membuat custom dashboard ClickHouse dari Odoo tanpa
coding ("Custom Reports"). Bagian dari OLAP Platform — lihat
`OLAP-ARCHITECTURE.md` §11 di repo `dev-olap-template` untuk konteks
lengkap arsitektur, dan `client-pilot-olap/README.md` untuk contoh
konfigurasi live.

**Status:** Sprint 6D selesai dan **terverifikasi live** — semua action
(Validate, Publish, Update, Unpublish, Open Dashboard) memanggil Go API
sungguhan lewat `requests`, sudah dites end-to-end di `odoo14-development`
(happy path: create → Validate & Preview → Publish → dashboard tampil data).

## Install (manual)

1. Copy folder ini ke `addons_path` server Odoo (mis. `custom/src/private/`
   pada project Doodba).
2. Restart Odoo, lalu **Settings → Apps → Update Apps List**.
3. Cari "OLAP Dashboard Builder" → Install (atau **Upgrade** kalau sudah
   pernah terinstall — wajib supaya `data/config_parameter_data.xml`
   ter-load).
4. Menu **OLAP → Dashboard Builder** akan muncul.

## Konfigurasi (wajib sebelum pakai)

System Parameters yang perlu diisi di Odoo (Settings → Technical → System
Parameters) — nilai default di `data/config_parameter_data.xml` cuma
placeholder, harus diganti sesuai deployment:

```
olap.go_api_url       = http://analytics-api:8090     # nama SERVICE Docker internal (bukan domain publik)
olap.go_dashboard_url = https://analytics.client.com  # domain publik dashboard
olap.go_api_key       = (sama dengan ODOO_API_KEY di .env server Go)
```

`olap.go_api_key` dikirim sebagai header `X-API-Key` di setiap request ke
Go API — harus persis sama dengan env var `ODOO_API_KEY` di deployment
`client-*-olap`/`olap-client-template` yang bersangkutan. Kalau tidak
sinkron, semua action (Validate/Publish/Update/Unpublish) gagal dengan
error 401 dari Go API.

`olap.go_api_url` **bukan** domain Traefik publik — harus nama service
Docker Compose Go API (mis. `analytics-api`) beserta port internalnya
(`8090`), karena dipanggil server-to-server dari dalam container Odoo, tidak
lewat browser/Traefik.

## Alur pakai

1. Menu **OLAP → Dashboard Builder** → buat record baru: isi nama, tipe
   chart, query ClickHouse (query harus `SELECT ...` dari database
   `odoo_analytics`, cek kolom X/Y kalau perlu)
2. **Validate & Preview** — Go jalankan query dengan `LIMIT 5`, tampil di
   tab Preview kalau berhasil. Query berbahaya (`DROP`/`ALTER`/dst) akan
   ditolak di sini dengan pesan error, state tetap Draft
3. **Publish** — Go simpan report permanen, dashboard-nya langsung bisa
   diakses (`go_report_id` terisi, muncul di sidebar "Custom Reports" Go)
4. **Open Dashboard** — buka tab baru ke dashboard Go. **Browser harus
   sudah login** ke dashboard Go (session cookie) — kalau belum pernah
   login di domain itu, akan diarahkan ke halaman login dulu
5. **Update** (kalau sudah Published) — edit query/config → simpan
   perubahan ke Go
6. **Unpublish** — hapus dari Go, state kembali ke Draft

## Troubleshooting

**Dashboard tampil tapi tidak ada data / chart kosong**
Bukan bug di modul ini — cek apakah tabel ClickHouse yang di-query benar-
benar punya data. Penyebab paling umum: modul Odoo terkait (mis. `sale`)
belum diinstall di database ini, jadi tabel PostgreSQL-nya tidak pernah ada
untuk di-capture Debezium. Lihat bagian Troubleshooting di
`client-pilot-olap/README.md` untuk cara cek lebih lanjut (termasuk cek
status task Debezium connector).

**Field Query error `mode.transformAction is not a function` saat diketik**
Sudah diperbaiki — field `ch_query` pakai `widget="text"` biasa, bukan
`widget="ace"`, karena Ace bawaan Odoo 14 tidak punya mode SQL. Kalau error
ini muncul lagi berarti ada perubahan yang tidak sengaja mengembalikan
`options="{'mode': 'sql'}"` di `views/olap_dashboard_views.xml`.

**Semua action gagal dengan "Gagal menghubungi Go API"**
`olap.go_api_url` biasanya salah isi — pastikan pakai nama service Docker
(`http://analytics-api:8090`), bukan domain publik/`localhost`. Bisa dites
manual dari dalam container Odoo:
```bash
docker exec <container_odoo> curl -s -o /dev/null -w '%{http_code}\n' \
  http://analytics-api:8090/api/custom-reports -H 'X-API-Key: <key>'
```
