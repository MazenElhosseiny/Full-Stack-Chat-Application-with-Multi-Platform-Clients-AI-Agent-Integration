Place your completed `index.html` from Week 4 in this directory.

In the Week 5 architecture, nginx serves static files from this directory
directly (see nginx.conf — the `location /` block serves from
`/usr/share/nginx/html`, which maps to this folder via the volume mount
in compose.yml).

The Flask API (`api/server.py`) no longer needs to serve the HTML page in
production — nginx handles that. Flask only handles /chat and /history.