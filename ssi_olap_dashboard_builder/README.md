# olap_dashboard_builder

Modul Odoo 14 untuk membuat custom dashboard ClickHouse dari Odoo tanpa
coding. Bagian dari OLAP Platform — lihat `OLAP-ARCHITECTURE.md` §11 di repo
`dev-olap-template` untuk konteks lengkap.

**Status:** Sprint 6C — model + views selesai. Tombol Validate/Publish/
Update/Unpublish/Open Dashboard masih stub (raise `UserError`), diimplementasikan
di Sprint 6D bersama pemanggilan Go API.

## Install (manual)

1. Copy folder ini ke `addons_path` server Odoo (mis. `custom/src/private/`
   pada project Doodba).
2. Restart Odoo, lalu **Settings → Apps → Update Apps List**.
3. Cari "OLAP Dashboard Builder" → Install.
4. Menu **OLAP → Dashboard Builder** akan muncul.

## Konfigurasi (dipakai mulai Sprint 6D)

System Parameters yang perlu diisi di Odoo (Settings → Technical → System
Parameters):

```
olap.go_api_url       = http://analytics:8090
olap.go_dashboard_url = https://analytics.client.com
```
