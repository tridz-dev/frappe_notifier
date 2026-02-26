import io
from pathlib import Path

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer


class ServiceWorkerRenderer(BaseRenderer):
    """Serve the Firebase messaging service worker at /firebase-messaging-sw.js.

    This lets us keep the actual file inside the app while exposing it
    from the origin root so the service worker scope covers the whole site.
    """

    def can_render(self) -> bool:
        # Handle exactly /firebase-messaging-sw.js (with or without leading slash)
        return self.path.strip("/") == "firebase-messaging-sw.js"

    def render(self):
        # Resolve the bundled SW file from this app's public folder.
        # We keep the source at frappe_notifier/public/sw.js
        app_public_path = Path(frappe.get_app_path("frappe_notifier", "public"))
        sw_path = app_public_path / "sw.js"

        if not sw_path.is_file():
            # If the file is missing, return a small no-op script to avoid hard failures.
            content = "// frappe_notifier: service worker script not found\n"
        else:
            # Read as UTF-8 text; the JS is plain text.
            with io.open(sw_path, mode="r", encoding="utf-8") as f:
                content = f.read()

        # BaseRenderer.build_response will set the correct JS mimetype for *.js paths,
        # so we override `path` to end with .js before building the response.
        original_path = self.path
        self.path = "firebase-messaging-sw.js"
        try:
            return self.build_response(content)
        finally:
            # Restore the original path for any downstream use.
            self.path = original_path

