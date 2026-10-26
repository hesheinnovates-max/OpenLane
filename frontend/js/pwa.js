// =========================================================
// Makes OpenLane installable as an app (PWA)
// - registers the service worker
// - shows "Install app" buttons ([data-install-app]) when the
//   phone / browser allows installing
// - on iPhone (Safari has no install prompt) explains
//   Share -> Add to Home Screen
// =========================================================

(() => {
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/sw.js").catch(error => console.warn("Service worker not registered:", error));
        });
    }

    const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
    const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    let installPrompt = null;

    function buttons() {
        return document.querySelectorAll("[data-install-app]");
    }

    function showButtons(show) {
        buttons().forEach(button => { button.hidden = !show; });
    }

    function iosHelp() {
        let box = document.getElementById("ios-install-help");
        if (!box) {
            box = document.createElement("div");
            box.id = "ios-install-help";
            box.className = "modal";
            box.setAttribute("role", "dialog");
            box.setAttribute("aria-modal", "true");
            box.innerHTML = `
                <div class="modal-box" style="max-width:420px">
                    <button class="modal-close" type="button" aria-label="Close">×</button>
                    <p class="eyebrow">Install OpenLane</p>
                    <h2>Add OpenLane to your Home Screen</h2>
                    <ol class="steps" style="list-style:none;margin-top:14px">
                        <li class="step" style="cursor:default"><div><strong>1. Tap the Share button</strong><span>The square with an arrow pointing up, in Safari's toolbar.</span></div></li>
                        <li class="step" style="cursor:default"><div><strong>2. Tap "Add to Home Screen"</strong><span>Scroll down the list if you don't see it.</span></div></li>
                        <li class="step" style="cursor:default"><div><strong>3. Tap "Add"</strong><span>OpenLane now opens from your Home Screen like an app.</span></div></li>
                    </ol>
                </div>`;
            document.body.appendChild(box);
            box.addEventListener("click", event => {
                if (event.target === box || event.target.closest(".modal-close")) {
                    box.classList.remove("open");
                    document.body.style.overflow = "";
                }
            });
        }
        box.classList.add("open");
        document.body.style.overflow = "hidden";
    }

    // Chrome / Edge / Samsung Internet on Android and desktop
    window.addEventListener("beforeinstallprompt", event => {
        event.preventDefault();
        installPrompt = event;
        showButtons(true);
    });

    window.addEventListener("appinstalled", () => {
        installPrompt = null;
        showButtons(false);
    });

    document.addEventListener("DOMContentLoaded", () => {
        if (isStandalone) {
            showButtons(false);
            return;
        }
        // Safari on iPhone never fires beforeinstallprompt, so show the button with instructions
        if (isIOS) showButtons(true);

        buttons().forEach(button => {
            button.addEventListener("click", async () => {
                if (installPrompt) {
                    installPrompt.prompt();
                    const choice = await installPrompt.userChoice;
                    if (choice.outcome === "accepted") showButtons(false);
                    installPrompt = null;
                } else if (isIOS) {
                    iosHelp();
                }
            });
        });
    });
})();
