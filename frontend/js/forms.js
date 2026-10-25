document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const errorBox = form.parentElement.querySelector("#form-error");

            if (errorBox) {
                errorBox.textContent = "";
                errorBox.classList.remove("show");
            }

            function showError(message) {
                if (!errorBox) {
                    return;
                }

                errorBox.textContent = message;
                errorBox.classList.add("show");
            }

            // Job Seekers must provide an email address or a phone number.
            if (form.hasAttribute("data-contact-check")) {
                const email = form.querySelector('[name="email"]').value.trim();
                const phone = form.querySelector('[name="phone"]').value.trim();

                if (!email && !phone) {
                    event.preventDefault();
                    showError("Please provide an email address or phone number.");
                    return;
                }
            }

            // This is a convenience check. The backend must validate passwords too.
            if (form.hasAttribute("data-password-check")) {
                const password = form.querySelector('[name="password"]').value;

                const hasUppercase = /[A-Z]/.test(password);
                const hasLowercase = /[a-z]/.test(password);
                const hasNumber = /[0-9]/.test(password);
                const hasSpecialCharacter = /[^a-zA-Z0-9]/.test(password);
                const hasMinimumLength = password.length >= 12;

                if (
                    !hasMinimumLength ||
                    !hasUppercase ||
                    !hasLowercase ||
                    !hasNumber ||
                    !hasSpecialCharacter
                ) {
                    event.preventDefault();

                    showError(
                        "Use at least 12 characters, including uppercase, lowercase, " +
                        "a number, and a special character."
                    );
                }
            }
        });
    });
});
