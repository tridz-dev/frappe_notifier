// firebase-messaging-sw.js
// Source file: frappe_notifier/public/sw.js
// Served at: /firebase-messaging-sw.js (via custom page_renderer)
//
// Firebase config is passed via ?config=<urlencoded JSON> when the SW is registered
// from push_bridge.js — because service workers cannot read frappe.boot directly.

importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js");

// ---------------------------------------------------------------------------
// Parse Firebase config injected into the SW URL by push_bridge.js
// ---------------------------------------------------------------------------
function getConfigFromURL() {
    try {
        const url = new URL(self.location.href);
        const raw = url.searchParams.get("config");
        if (raw) return JSON.parse(decodeURIComponent(raw));
    } catch (e) {
        console.error("[frappe_notifier SW] Failed to parse config from URL:", e);
    }
    return null;
}

const firebaseConfig = getConfigFromURL();

if (firebaseConfig) {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // -----------------------------------------------------------------------
    // Background message handler
    // Fires when a push arrives and the Desk tab is NOT in the foreground.
    // -----------------------------------------------------------------------
    messaging.onBackgroundMessage(function (payload) {
        console.log("[frappe_notifier SW] Background message received:", payload);

        const data  = payload.data         || {};
        const notif = payload.notification  || {};

        const title        = notif.title        || data.title        || "New Notification";
        const body         = notif.body         || data.body         || "";
        const icon         = notif.icon         || data.icon         || "/assets/frappe/images/frappe-framework-logo.svg";
        const click_action = data.click_action  || notif.click_action || "/";

        return self.registration.showNotification(title, {
            body,
            icon,
            badge: icon,
            data: { click_action },
            requireInteraction: false,
        });
    });
} else {
    console.warn("[frappe_notifier SW] No firebase config found — background notifications will not work.");
}

// ---------------------------------------------------------------------------
// Notification click handler — navigate to click_action URL
// ---------------------------------------------------------------------------
self.addEventListener("notificationclick", function (event) {
    event.notification.close();

    const url = (event.notification.data && event.notification.data.click_action) || "/";

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (list) {
            for (const client of list) {
                if ("focus" in client) {
                    client.focus();
                    if ("navigate" in client) client.navigate(url);
                    return;
                }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});