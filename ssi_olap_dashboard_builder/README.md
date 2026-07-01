# olap_dashboard_builder

Modul Odoo 14 untuk membuat custom dashboard ClickHouse dari Odoo tanpa
coding. Bagian dari OLAP Platform — lihat `OLAP-ARCHITECTURE.md` §11 di repo
`dev-olap-template` untuk konteks lengkap.

**Status:** Sprint 6D — semua action (Validate, Publish, Update, Unpublish,
Open Dashboard) sudah memanggil Go API sungguhan lewat `requests`.

## Install (manual)

1. Copy folder ini ke `addons_path` server Odoo (mis. `custom/src/private/`
   pada project Doodba).
2. Restart Odoo, lalu **Settings → Apps → Update Apps List**.
3. Cari "OLAP Dashboard Builder" → Install.
4. Menu **OLAP → Dashboard Builder** akan muncul.

## Konfigurasi (wajib sebelum pakai)

System Parameters yang perlu diisi di Odoo (Settings → Technical → System
Parameters) — nilai default di `data/config_parameter_data.xml` cuma
placeholder, harus diganti sesuai deployment:

```
olap.go_api_url       = http://analytics:8090        # network internal, host:port service Go
olap.go_dashboard_url = https://analytics.client.com # domain publik dashboard
olap.go_api_key       = (sama dengan ODOO_API_KEY di .env server Go)
```

`olap.go_api_key` dikirim sebagai header `X-API-Key` di setiap request ke
Go API — harus persis sama dengan env var `ODOO_API_KEY` di deployment
`client-*-olap`/`olap-client-template` yang bersangkutan.
