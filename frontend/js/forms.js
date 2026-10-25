const companyForm = document.getElementById("company-register-form");
const jobSeekerForm = document.getElementById("job-seeker-register-form");

function showMessage(element, text, type) {
    clearTimeout(element.messageTimer);

    element.classList.remove("show");

    element.messageTimer = setTimeout(() => {
        element.textContent = text;

        element.className = type;

        requestAnimationFrame(() => {
            element.classList.add("show");
        });

        element.messageTimer = setTimeout(() => {
            element.classList.remove("show");
        }, 5000);

    }, 350);
}


async function handleRegistration(event) {
    event.preventDefault();

    const form = event.currentTarget;

    const message = form.querySelector("#form-message");

    const submitButton = form.querySelector(
        'button[type="submit"]'
    );

    if (!message || !submitButton) {
        console.error(
            "Registration form is missing its message element or submit button."
        );
        return;
    }

    submitButton.disabled = true;

    const originalButtonText = submitButton.textContent;

    submitButton.textContent = "Creating account...";

    clearTimeout(message.messageTimer);
    clearTimeout(message.hideTimer);

    message.classList.remove("show");
    message.textContent = "";

    try {
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form)
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(
                message,
                result.message || "Registration successful.",
                "success"
            );

            form.reset();

        } else {
            showMessage(
                message,
                result.detail || "Registration failed. Please try again.",
                "error"
            );
        }

    } catch (error) {
        console.error("Registration request failed:", error);

        showMessage(
            message,
            "Could not contact the server. Please try again.",
            "error"
        );

    } finally {
        submitButton.disabled = false;

        submitButton.textContent = originalButtonText;
    }
}

if (jobSeekerForm) {
    jobSeekerForm.addEventListener(
        "submit",
        handleRegistration
    );
}

if (companyForm) {
    companyForm.addEventListener(
        "submit",
        handleRegistration
    );
}

