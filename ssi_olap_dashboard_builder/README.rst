.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
OLAP Dashboard Builder
=======================

Build custom ClickHouse analytics dashboards directly from Odoo, without
writing code. This module is part of the OLAP Platform: reports created and
published here automatically appear in the "Custom Reports" section of the
Go dashboard service.


Configuration
=============

Before use, the following System Parameters must be set (Settings >
Technical > System Parameters). The defaults shipped in
``data/config_parameter_data.xml`` are placeholders only:

.. code-block::

    olap.go_api_url       = http://analytics-api:8090     # internal Docker service name, not a public domain
    olap.go_dashboard_url = https://analytics.client.com   # public dashboard domain
    olap.go_api_key       = (must match ODOO_API_KEY in the Go server's .env)

``olap.go_api_key`` is sent as the ``X-API-Key`` header on every request to
the Go API. If it does not match the Go deployment's ``ODOO_API_KEY``, every
action (Validate/Publish/Update/Unpublish) fails with a 401 error.

``olap.go_api_url`` is **not** the public Traefik domain - it must be the
Docker Compose service name and internal port of the Go API (e.g.
``analytics-api:8090``), since it is called server-to-server from inside the
Odoo container, not through the browser/Traefik.


Usage
=====

#. Menu **OLAP > Dashboard Builder** - create a new record: name, chart
   type, ClickHouse query (must be a ``SELECT`` against the
   ``odoo_analytics`` database, plus X/Y columns if needed).
#. **Validate & Preview** - the Go API runs the query with ``LIMIT 5`` and
   shows the result in the Preview tab on success. Dangerous queries
   (``DROP``/``ALTER``/etc.) are rejected here with an error message; the
   state stays Draft.
#. **Publish** - the Go API stores the report permanently; it becomes
   immediately reachable (``go_report_id`` is filled in and the report shows
   up in the Go dashboard's "Custom Reports" sidebar).
#. **Open Dashboard** - opens a new tab to the Go dashboard. The browser
   must already be logged in to the Go dashboard (session cookie); otherwise
   it will redirect to a login page.
#. **Update** (only when Published) - edit the query/config, then save the
   change to Go.
#. **Unpublish** - removes the report from Go; the state goes back to Draft.


Installation
============

To install this module, you need to:

1.  Clone the branch 14.0 of the repository https://github.com/mikevhe18/ssi-olap
2.  Add the path to this repository in your configuration (addons-path)
3.  Update the module list (Must be on developer mode)
4.  Go to menu *Apps -> Apps -> Main Apps*
5.  Search For *OLAP Dashboard Builder*
6.  Install the module


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/mikevhe18/ssi-olap/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it
first, help us smash it by providing detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Michael Viriyananda <viriyananda.michael@gmail.com>

Maintainer
----------

.. image:: https://simetri-sinergi.id/logo.png
   :alt: PT. Simetri Sinergi Indonesia
   :target: https://simetri-sinergi.id

This module is maintained by the PT. Simetri Sinergi Indonesia.
