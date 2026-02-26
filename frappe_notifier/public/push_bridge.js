

console.log("[push_bridge] loaded");

// via a custom Frappe page_renderer (see frappe_notifier/service_worker.py).
const SW_PATH    = "/firebase-messaging-sw.js";
const TOKEN_KEY  = "frappe_notifier_fcm_token";
const BTN_ID     = "push-notif-toggle-btn";
const PROJECT_NAME = "frappe_desk";
// ---------------------------------------------------------------------------
// Read config from frappe.boot (injected by frappe_notifier/boot.py)
// Expected shape:
//   frappe.boot.frappe_notifier = {
//       firebase_config: { apiKey, authDomain, projectId, storageBucket, messagingSenderId, appId },
//       vapid_public_key: "Bxxx...",
//   }
// ---------------------------------------------------------------------------
function getBootConfig() {
    const cfg = frappe.boot && frappe.boot.frappe_notifier;
    if (!cfg || !cfg.firebase_config || !cfg.vapid_public_key) {
        console.error("[push_bridge] frappe.boot.frappe_notifier is missing or incomplete.", cfg);
        return null;
    }
    // firebase_config may be stored as a JSON string in the doctype field
    let firebaseConfig = cfg.firebase_config;
    if (typeof firebaseConfig === "string") {
        try { firebaseConfig = JSON.parse(firebaseConfig); }
        catch (e) { console.error("[push_bridge] Failed to parse firebase_config JSON:", e); return null; }
    }
    return {
        firebaseConfig,
        vapidPublicKey: cfg.vapid_public_key,
    };
}

async function getServiceWorkerRegistration(firebaseConfig) {
    if (!("serviceWorker" in navigator)) {
        throw new Error("Service workers are not supported by this browser.");
    }
    const encodedConfig = encodeURIComponent(JSON.stringify(firebaseConfig));
    const swURL = `${SW_PATH}?config=${encodedConfig}`;

    // Check if already registered to avoid duplicate registrations
    const existing = await navigator.serviceWorker.getRegistrations();
    for (const reg of existing) {
        if (reg.active && reg.active.scriptURL && reg.active.scriptURL.includes("firebase-messaging-sw.js")) {
            console.log("[push_bridge] Reusing existing SW registration.");
            return reg;
        }
    }
    console.log("[push_bridge] Registering new service worker...");
    return navigator.serviceWorker.register(swURL, { scope: "/" });
}

async function subscribeToken(token) {
    const res = await fetch(`/api/method/frappe.push_notification.subscribe?fcm_token=${token}&project_name=${PROJECT_NAME}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });
    return res.ok;
}

async function unsubscribeToken(token) {
    const res = await fetch(`/api/method/frappe.push_notification.unsubscribe?fcm_token=${token}&project_name=${PROJECT_NAME}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });
    return res.ok;
}

function updateButtonLabel(isEnabled) {
    const btn = document.getElementById(BTN_ID);
    if (btn) {
        btn.textContent = isEnabled
            ? __("Disable Push Notifications")
            : __("Enable Push Notifications");
    }
}

async function enablePushForDesk() {
    // Dynamic ESM import — no build step needed
    const { initializeApp, getApps, getApp } = await import("https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js");
    const { getMessaging, getToken, deleteToken, onMessage, isSupported } = await import("https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging.js");

    // Check browser support
    if (!await isSupported()) {
        frappe.msgprint({
            title: __("Not Supported"),
            message: __("Push notifications are not supported in this browser."),
            indicator: "red",
        });
        return;
    }

    const bootConfig = getBootConfig();
    if (!bootConfig) {
        frappe.msgprint({
            title: __("Configuration Error"),
            message: __("Firebase configuration is missing. Please check Frappe Notifier Settings."),
            indicator: "red",
        });
        return;
    }

    const { firebaseConfig, vapidPublicKey } = bootConfig;
    const existingToken = localStorage.getItem(TOKEN_KEY);

    // ---- DISABLE path ----
    if (existingToken) {
        try {
            const app = getApps().length ? getApp("frappe-notifier") : initializeApp(firebaseConfig, "frappe-notifier");
            const messaging = getMessaging(app);
            await deleteToken(messaging).catch(() => {});
            await unsubscribeToken(existingToken);
        } catch (e) {
            console.error("[push_bridge] Error during disable:", e);
        }
        localStorage.removeItem(TOKEN_KEY);
        updateButtonLabel(false);
        frappe.show_alert({ message: __("Push notifications disabled"), indicator: "orange" }, 4);
        return;
    }

    // ---- ENABLE path ----

    // 1. Request browser permission
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
        frappe.show_alert({ message: __("Notification permission was denied"), indicator: "red" }, 4);
        return;
    }

    frappe.show_alert({ message: __("Setting up push notifications…"), indicator: "blue" }, 3);

    try {
        // 2. Register service worker
        const swReg = await getServiceWorkerRegistration(firebaseConfig);

        // 3. Initialize Firebase (reuse existing app instance if already created)
        let app;
        try { app = getApp("frappe-notifier"); }
        catch (_) { app = initializeApp(firebaseConfig, "frappe-notifier"); }

        const messaging = getMessaging(app);

        // 4. Get FCM token
        const newToken = await getToken(messaging, {
            vapidKey: vapidPublicKey,
            serviceWorkerRegistration: swReg,
        });

        if (!newToken) throw new Error("getToken returned empty token");

        // 5. If token changed, unsubscribe old one first
        const oldToken = localStorage.getItem(TOKEN_KEY);
        if (oldToken && oldToken !== newToken) {
            await unsubscribeToken(oldToken).catch(() => {});
        }

        // 6. Subscribe new token with Frappe
        const ok = await subscribeToken(newToken);
        if (!ok) throw new Error("Frappe subscribe endpoint returned an error");

        // 7. Save token locally
        localStorage.setItem(TOKEN_KEY, newToken);
        updateButtonLabel(true);
        frappe.show_alert({ message: __("Push notifications enabled!"), indicator: "green" }, 4);

        // 8. Handle foreground messages (when Desk tab IS open)
        onMessage(messaging, (payload) => {
            console.log("[push_bridge] Foreground message:", payload);
            const data  = payload.data || {};
            const notif = payload.notification  || {};
            const title = notif.title || data.title || __("Notification");
            const body  = notif.body  || data.body  || "";
            frappe.show_alert({
                message: `<b>${title}</b>${body ? "<br>" + body : ""}`,
                indicator: "blue",
            }, 8);
        });

    } catch (err) {
        console.error("[push_bridge] Error enabling push notifications:", err);
        frappe.show_alert({
            message: __("Failed to enable push notifications: ") + err.message,
            indicator: "red",
        }, 6);
    }
}

frappe.after_ajax(function () {
    // Ensure config object exists before checking any flags
    if (!frappe.boot || !frappe.boot.frappe_notifier) {
        console.warn("[push_bridge] frappe.boot.frappe_notifier not found — skipping menu injection");
        return;
    }

    if (!frappe.boot.frappe_notifier.push_notifications_enabled) {
        console.log("[push_bridge] push_notifications_enabled is false — skipping menu injection");
        return;
    }

    $(document).on("toolbar_setup", function () {
        // Guard against double injection (e.g. on route change)
        if (document.getElementById(BTN_ID)) return;

        const isEnabled = !!localStorage.getItem(TOKEN_KEY);

        const $btn = $(`
            <button class="btn-reset dropdown-item" id="${BTN_ID}">
                ${isEnabled ? __("Disable Push Notifications") : __("Enable Push Notifications")}
            </button>
        `);

        $btn.on("click", function () {
            // Close the dropdown
            $(".dropdown-user").removeClass("show");
            $(".dropdown-user .dropdown-menu").removeClass("show");
            enablePushForDesk();
        });

        const $menu = $("#toolbar-user");
        const $divider = $menu.find(".dropdown-divider").first();

        if ($divider.length) {
            $btn.insertBefore($divider);
        } else {
            $menu.append($btn);
        }

        console.log("[push_bridge] Menu item injected. Currently enabled:", isEnabled);
    });
});