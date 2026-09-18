"""WSGI entry point for the isolated, single-proxy public deployment."""
from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app as create_diana_app


def create_app():
    app = create_diana_app()
    # Caddy replaces X-Forwarded-For and X-Forwarded-Proto. This entry point must
    # only be reachable on the private Docker network, never via a public port.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)
    return app
