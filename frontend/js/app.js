// =========================================================
// Shared helpers for the OpenLane dashboards and job pages
// =========================================================

const OpenLane = (() => {
    // Escape text before putting it inside HTML
    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // Call the backend. Sends FormData, returns JSON or throws an Error with a readable message.
    async function api(url, { method = "GET", data = null } = {}) {
        const options = { method, headers: { "Accept": "application/json" }, credentials: "same-origin" };
        if (data) {
            const body = data instanceof FormData ? data : new FormData();
            if (!(data instanceof FormData)) {
                Object.entries(data).forEach(([key, value]) => body.append(key, value ?? ""));
            }
            options.body = body;
        }

        let response;
        try {
            response = await fetch(url, options);
        } catch (error) {
            throw new Error("Could not contact the server. Check your connection and try again.");
        }

        let result = {};
        const type = response.headers.get("content-type") || "";
        if (type.includes("application/json")) result = await response.json();

        if (response.status === 401) {
            const error = new Error(result.detail || "Your session has ended. Please log in again.");
            error.status = 401;
            throw error;
        }
        if (!response.ok) {
            const error = new Error(typeof result.detail === "string" ? result.detail : `Something went wrong (${response.status}). Please try again.`);
            error.status = response.status;
            throw error;
        }
        return result;
    }

    // Small message at the bottom of the screen
    let toastTimer;
    function toast(message, type = "success") {
        let element = document.getElementById("toast");
        if (!element) {
            element = document.createElement("div");
            element.id = "toast";
            element.className = "toast";
            element.setAttribute("role", "status");
            element.setAttribute("aria-live", "polite");
            document.body.appendChild(element);
        }
        clearTimeout(toastTimer);
        element.textContent = message;
        element.className = `toast ${type}`;
        requestAnimationFrame(() => element.classList.add("show"));
        toastTimer = setTimeout(() => element.classList.remove("show"), type === "error" ? 6000 : 3500);
    }

    function formatDate(iso) {
        if (!iso) return "";
        const date = new Date(iso);
        return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
    }

    function timeAgo(iso) {
        if (!iso) return "";
        const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
        if (seconds < 60) return "just now";
        const minutes = Math.round(seconds / 60);
        if (minutes < 60) return `${minutes} min ago`;
        const hours = Math.round(minutes / 60);
        if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
        const days = Math.round(hours / 24);
        if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
        return formatDate(iso);
    }

    function badge(status) {
        const css = String(status || "").toLowerCase().replace(/\s+/g, "-");
        return `<span class="badge ${escapeHtml(css)}">${escapeHtml(status)}</span>`;
    }

    // Progress bar with the number written next to it (not colour only)
    function progressBar(value, { big = false, label = "" } = {}) {
        if (value === null || value === undefined) {
            return `<p class="small muted">Progress unavailable: this skill has no learning steps yet.</p>`;
        }
        const safe = Math.max(0, Math.min(100, value));
        return `
            <div class="progress-row">
                <div class="progress ${big ? "big" : ""}" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${safe}" aria-label="${escapeHtml(label || "Progress")}">
                    <div class="progress-fill" style="width:${safe}%"></div>
                </div>
                <span class="progress-value">${safe}%</span>
            </div>`;
    }

    // ---------- Tabs ----------
    function setupTabs(onChange) {
        const tabs = document.querySelectorAll("[data-tab]");
        function show(name, push = true) {
            const panel = document.getElementById(`panel-${name}`);
            if (!panel) return;
            tabs.forEach(tab => {
                const active = tab.dataset.tab === name;
                tab.classList.toggle("active", active);
                tab.setAttribute("aria-selected", active ? "true" : "false");
            });
            document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p === panel));
            if (push) history.replaceState(null, "", `#${name}`);
            if (onChange) onChange(name);
        }
        tabs.forEach(tab => tab.addEventListener("click", () => show(tab.dataset.tab)));
        document.querySelectorAll("[data-go]").forEach(link => {
            link.addEventListener("click", event => {
                event.preventDefault();
                show(link.dataset.go);
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        });
        const first = location.hash.replace("#", "") || tabs[0]?.dataset.tab;
        show(document.getElementById(`panel-${first}`) ? first : tabs[0]?.dataset.tab, false);
        return show;
    }

    // ---------- Modal ----------
    function openModal(id) {
        const modal = document.getElementById(id);
        if (!modal) return;
        modal.classList.add("open");
        document.body.style.overflow = "hidden";
        modal.querySelector(".modal-close")?.focus();
    }

    function closeModal(id) {
        const modal = typeof id === "string" ? document.getElementById(id) : id;
        if (!modal) return;
        modal.classList.remove("open");
        document.body.style.overflow = "";
    }

    document.addEventListener("click", event => {
        if (event.target.classList.contains("modal")) closeModal(event.target);
        if (event.target.closest(".modal-close")) closeModal(event.target.closest(".modal"));
    });
    document.addEventListener("keydown", event => {
        if (event.key === "Escape") document.querySelectorAll(".modal.open").forEach(closeModal);
    });

    // Disable a button while a request runs
    async function withButton(button, text, work) {
        const original = button ? button.textContent : "";
        if (button) {
            button.disabled = true;
            button.textContent = text;
        }
        try {
            return await work();
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = original;
            }
        }
    }

    function handleError(error, loginUrl) {
        if (error.status === 401 && loginUrl) {
            toast("Your session has ended. Please log in again.", "error");
            setTimeout(() => { window.location.href = loginUrl; }, 1200);
            return;
        }
        toast(error.message, "error");
    }

    // Ask the user to confirm an action (used instead of the browser's confirm box)
    function confirmAction({ title, text, confirmLabel = "Confirm", danger = false }) {
        return new Promise(resolve => {
            let modal = document.getElementById("confirm-modal");
            if (!modal) {
                modal = document.createElement("div");
                modal.id = "confirm-modal";
                modal.className = "modal";
                modal.setAttribute("role", "alertdialog");
                modal.setAttribute("aria-modal", "true");
                document.body.appendChild(modal);
            }
            modal.innerHTML = `
                <div class="modal-box" style="max-width:440px">
                    <h2>${escapeHtml(title)}</h2>
                    <p class="intro" style="margin-bottom:18px">${escapeHtml(text)}</p>
                    <div class="form-actions">
                        <button type="button" class="btn btn-inline ${danger ? "btn-danger" : ""}" data-answer="yes">${escapeHtml(confirmLabel)}</button>
                        <button type="button" class="btn btn-inline btn-secondary" data-answer="no">Cancel</button>
                    </div>
                </div>`;
            const finish = answer => {
                closeModal(modal);
                modal.removeEventListener("click", onClick);
                resolve(answer);
            };
            const onClick = event => {
                const button = event.target.closest("[data-answer]");
                if (button) finish(button.dataset.answer === "yes");
                else if (event.target === modal) finish(false);
            };
            modal.addEventListener("click", onClick);
            openModal("confirm-modal");
            modal.querySelector("[data-answer='no']").focus();
        });
    }

    return { escapeHtml, api, toast, formatDate, timeAgo, badge, progressBar, setupTabs, openModal, closeModal, withButton, handleError, confirmAction };
})();
