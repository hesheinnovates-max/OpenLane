document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("form");

    function passwordRequirements(value) {
        return {
            length: value.length >= 12,
            uppercase: /[A-Z]/.test(value),
            lowercase: /[a-z]/.test(value),
            number: /[0-9]/.test(value),
            special: /[^a-zA-Z0-9]/.test(value)
        };
    }

    function showMessage(element, text, type) {
        if (!element) return;
        clearTimeout(element.messageTimer);
        element.classList.remove("show", "success", "error");
        element.textContent = text;
        element.classList.add(type);
        requestAnimationFrame(() => element.classList.add("show"));
        // Keep errors visible long enough to read; fade either type after 6 seconds.
        element.messageTimer = setTimeout(() => element.classList.remove("show"), 6000);
    }

    function validatePasswordForm(form) {
        const password = form.querySelector("[data-password-field]");
        if (!password) return true;

        const confirmation = form.querySelector("[data-confirm-password]");
        const counter = form.querySelector("[data-password-counter]");
        const strength = form.querySelector("[data-password-strength]");
        const matchError = form.querySelector("[data-password-match-error]");
        const rules = passwordRequirements(password.value);

        if (counter) counter.textContent = `${password.value.length} / 12+ chars`;
        Object.entries(rules).forEach(([name, valid]) => {
            const item = form.querySelector(`[data-requirement="${name}"]`);
            if (item) item.classList.toggle("valid", valid);
        });

        const score = Object.values(rules).filter(Boolean).length;
        if (strength) {
            strength.style.width = `${score * 20}%`;
            strength.style.backgroundColor = score <= 2 ? "#dc2626" : score <= 4 ? "#d97706" : "#0a7a4b";
        }

        const passwordsMatch = !confirmation || (confirmation.value.length > 0 && confirmation.value === password.value);
        if (matchError) {
            matchError.classList.toggle("show", Boolean(confirmation && confirmation.value && !passwordsMatch));
        }
        return Object.values(rules).every(Boolean) && passwordsMatch;
    }

    // Show / hide password buttons.
    document.querySelectorAll("[data-toggle-password]").forEach(button => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.togglePassword);
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            button.textContent = show ? "Hide" : "Show";
            button.setAttribute("aria-label", `${show ? "Hide" : "Show"} password`);
        });
    });

    forms.forEach(form => {
        const password = form.querySelector("[data-password-field]");
        const confirmation = form.querySelector("[data-confirm-password]");
        const errorBox = form.querySelector("#form-error");
        const message = form.querySelector("#form-message");
        const submitButton = form.querySelector('button[type="submit"]');

        if (password) {
            password.addEventListener("input", () => validatePasswordForm(form));
            if (confirmation) confirmation.addEventListener("input", () => validatePasswordForm(form));
        }

        form.addEventListener("submit", async event => {
            if (errorBox) {
                errorBox.textContent = "";
                errorBox.classList.remove("show");
            }

            const showFormError = text => {
                if (!errorBox) return;
                errorBox.textContent = text;
                errorBox.classList.add("show");
            };

            if (form.hasAttribute("data-contact-check")) {
                const email = form.querySelector('[name="email"]')?.value.trim() || "";
                const phone = form.querySelector('[name="phone"]')?.value.trim() || "";
                if (!email && !phone) {
                    event.preventDefault();
                    showFormError("Please provide an email address or a phone number.");
                    return;
                }
            }

            if (form.hasAttribute("data-password-check") && !validatePasswordForm(form)) {
                event.preventDefault();
                showFormError("Please meet all password requirements and make sure both passwords match.");
                return;
            }

            // Forms marked data-ajax-submit stay on the page and display backend messages inline.
            if (!form.hasAttribute("data-ajax-submit")) return;
            event.preventDefault();

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.dataset.originalText = submitButton.textContent;
                submitButton.textContent = "Please wait...";
            }

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: { "Accept": "application/json" }
                });

                const contentType = response.headers.get("content-type") || "";
                let result = {};
                if (contentType.includes("application/json")) {
                    result = await response.json();
                } else {
                    // Avoid putting a raw HTML error page into the message area.
                    await response.text();
                    if (!response.ok) {
                        result = { detail: `The request failed (${response.status}). Please check the endpoint and try again.` };
                    } else {
                        result = { message: "Request completed." };
                    }
                }

                if (!response.ok) {
                    const detail = typeof result.detail === "string" ? result.detail : "Request failed. Please check your details and try again.";
                    showMessage(message, detail, "error");
                } else {
                    showMessage(message, result.message || "Request completed successfully.", "success");
                    if (!form.hasAttribute("data-reset-password")) form.reset();
                    if (password) validatePasswordForm(form);
                }
            } catch (error) {
                console.error("OpenLane form submission failed:", error);
                showMessage(message, error.message || "Could not contact the server. Please try again.", "error");
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = submitButton.dataset.originalText || "Submit";
                }
            }
        });
    });
});