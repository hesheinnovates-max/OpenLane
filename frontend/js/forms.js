const companyForm = document.getElementById("company-register-form");
const jobSeekerForm = document.getElementById("job-seeker-register-form");

function showMessage(element, text, type) {
    // Cancel any pending message timer.
    clearTimeout(element.messageTimer);

    // Hide the previous message before replacing it.
    element.classList.remove("show");

    // Wait for the fade-out transition to finish.
    element.messageTimer = setTimeout(() => {
        element.textContent = text;

        // Apply the success or error styling.
        element.className = type;

        // Make the message visible and animate it.
        requestAnimationFrame(() => {
            element.classList.add("show");
        });

        // Hide the message after five seconds.
        element.messageTimer = setTimeout(() => {
            element.classList.remove("show");
        }, 5000);

    }, 350);
}


/*
 * Handle registration for either form.
 */
async function handleRegistration(event) {
    // Stop the browser from navigating to the JSON response.
    event.preventDefault();

    const form = event.currentTarget;

    // Find the message element inside this specific form.
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

    // Prevent repeated submissions while the request is processing.
    submitButton.disabled = true;

    const originalButtonText = submitButton.textContent;

    submitButton.textContent = "Creating account...";

    // Clear any previous message.
    clearTimeout(message.messageTimer);
    clearTimeout(message.hideTimer);

    message.classList.remove("show");
    message.textContent = "";

    try {
        // Send the form data to the FastAPI endpoint.
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form)
        });

        // Read the JSON returned by FastAPI.
        const result = await response.json();

        if (response.ok) {
            showMessage(
                message,
                result.message || "Registration successful.",
                "success"
            );

            // Clear the form after successful registration.
            form.reset();

        } else {
            // Display backend validation errors, including HTTP 409.
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
        // Re-enable the button whether the request succeeds or fails.
        submitButton.disabled = false;

        submitButton.textContent = originalButtonText;
    }
}


/*
 * Attach the handler only to forms that exist on the current page.
 */
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

