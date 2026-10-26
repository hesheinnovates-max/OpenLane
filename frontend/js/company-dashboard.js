// =========================================================
// Company dashboard: jobs, applications and company profile
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    const { api, toast, escapeHtml, badge, formatDate, timeAgo, withButton, handleError, confirmAction, openModal } = OpenLane;
    const LOGIN = "/company/login";

    const state = {
        overview: null,
        jobs: [],
        applications: [],
    };

    const $ = id => document.getElementById(id);
    const fail = error => handleError(error, LOGIN);

    const showTab = OpenLane.setupTabs(name => {
        if (name === "post" && !$("job_id").value) resetJobForm();
    });

    // ---------------------------------------------------------
    // Loading data
    // ---------------------------------------------------------

    async function loadOverview() {
        state.overview = await api("/api/company/overview");
        renderOverview();
    }

    async function loadJobs() {
        state.jobs = await api("/api/company/jobs");
        renderJobs();
        renderJobFilterForApplications();
        renderGettingStarted();
    }

    async function loadApplications() {
        state.applications = await api("/api/company/applications");
        renderApplications();
        renderRecentApplications();
    }

    async function refreshAll() {
        try {
            await loadOverview();
            await Promise.all([loadJobs(), loadApplications()]);
        } catch (error) {
            fail(error);
        }
    }

    // ---------------------------------------------------------
    // Overview
    // ---------------------------------------------------------

    function renderOverview() {
        const { company, stats, businesses, job_types, application_statuses } = state.overview;
        $("top-company-name").textContent = company.company_name;
        $("welcome").textContent = `Welcome, ${company.company_name}`;
        document.querySelectorAll("[data-stat]").forEach(el => {
            el.textContent = stats[el.dataset.stat] ?? 0;
        });
        $("count-jobs").textContent = stats.jobs;
        $("count-pending").textContent = stats.applications;

        // Job form selects
        const businessSelect = $("job-business");
        const current = businessSelect.value;
        businessSelect.innerHTML = businesses.map(b => `<option value="${b.id}">${escapeHtml(b.name)}</option>`).join("");
        if (current) businessSelect.value = current;

        const typeSelect = $("job-type");
        if (typeSelect.options.length <= 1) {
            typeSelect.insertAdjacentHTML("beforeend", job_types.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join(""));
        }

        const businessFilter = $("job-business-filter");
        const filterValue = businessFilter.value;
        businessFilter.innerHTML = `<option value="">All businesses</option>` + businesses.map(b => `<option value="${b.id}">${escapeHtml(b.name)}</option>`).join("");
        businessFilter.value = filterValue;
        businessFilter.hidden = businesses.length < 2;

        const statusFilter = $("app-status-filter");
        if (statusFilter.options.length <= 1) {
            statusFilter.insertAdjacentHTML("beforeend", application_statuses.map(s => `<option value="${s}">${s[0].toUpperCase() + s.slice(1)}</option>`).join(""));
        }

        fillProfileForm(company);
        renderBusinesses(businesses);
    }

    function renderGettingStarted() {
        if (!state.overview) return;
        const company = state.overview.company;
        const items = [
            { done: Boolean(company.description), title: "Complete your company profile", text: "Add a short description so job seekers know who you are.", go: "profile" },
            { done: state.jobs.length > 0, title: "Create your first job", text: "Add a title, description and requirements.", go: "post" },
            { done: state.jobs.some(j => j.status === "published"), title: "Publish a job", text: "Published jobs appear in the job seeker discovery area.", go: "jobs" },
        ];
        $("getting-started").innerHTML = items.map(item => `
            <a class="step ${item.done ? "done" : ""}" href="#${item.go}" data-go-link="${item.go}" style="text-decoration:none;color:inherit">
                <input type="checkbox" ${item.done ? "checked" : ""} disabled aria-label="${item.done ? "Done" : "Not done"}">
                <div>
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${item.done ? "Done" : escapeHtml(item.text)}</span>
                </div>
            </a>`).join("");
    }

    $("getting-started").addEventListener("click", event => {
        const link = event.target.closest("[data-go-link]");
        if (!link) return;
        event.preventDefault();
        showTab(link.dataset.goLink);
    });

    function renderRecentApplications() {
        const recent = state.applications.slice(0, 5);
        if (!recent.length) {
            $("recent-applications").innerHTML = `
                <div class="empty">
                    <strong>No applications yet</strong>
                    Once you publish a job, applications from job seekers will appear here.
                </div>`;
            return;
        }
        $("recent-applications").innerHTML = recent.map(app => `
            <div class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(app.applicant.full_name)}</div>
                        <div class="item-meta"><span>Applied for ${escapeHtml(app.job.title)}</span><span>${timeAgo(app.created_at)}</span></div>
                    </div>
                    ${badge(app.status)}
                </div>
            </div>`).join("");
    }

    // ---------------------------------------------------------
    // Jobs list
    // ---------------------------------------------------------

    function renderJobs() {
        const search = $("job-search").value.trim().toLowerCase();
        const status = $("job-status-filter").value;
        const business = $("job-business-filter").value;
        const jobs = state.jobs.filter(job =>
            (!status || job.status === status) &&
            (!business || String(job.business.id) === business) &&
            (!search || `${job.title} ${job.location} ${job.job_type}`.toLowerCase().includes(search))
        );

        if (!state.jobs.length) {
            $("jobs-list").innerHTML = `
                <div class="empty">
                    <strong>You have not posted any jobs yet</strong>
                    Create your first opportunity so job seekers can find you.
                    <div><button class="btn btn-inline" type="button" data-action="new">+ Post a job</button></div>
                </div>`;
            return;
        }
        if (!jobs.length) {
            $("jobs-list").innerHTML = `<div class="empty"><strong>No jobs match your filters</strong>Try a different search or status.</div>`;
            return;
        }

        $("jobs-list").innerHTML = jobs.map(job => {
            const statusButtons = {
                draft: `<button class="btn btn-small" type="button" data-action="status" data-status="published" data-id="${job.id}">Publish</button>`,
                published: `<button class="btn btn-small btn-secondary" type="button" data-action="status" data-status="draft" data-id="${job.id}">Unpublish</button>
                            <button class="btn btn-small btn-secondary" type="button" data-action="status" data-status="closed" data-id="${job.id}">Close</button>`,
                closed: `<button class="btn btn-small btn-secondary" type="button" data-action="status" data-status="published" data-id="${job.id}">Reopen</button>`,
            }[job.status] || "";
            return `
            <article class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(job.title)}</div>
                        <div class="item-meta">
                            <span>${escapeHtml(job.business.name)}</span>
                            ${job.job_type ? `<span>${escapeHtml(job.job_type)}</span>` : ""}
                            ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ""}
                            <span>Posted ${formatDate(job.created_at)}</span>
                        </div>
                    </div>
                    ${badge(job.status)}
                </div>
                <p class="item-text clamp">${escapeHtml(job.description)}</p>
                <div class="actions">
                    ${statusButtons}
                    <button class="btn btn-small btn-secondary" type="button" data-action="edit" data-id="${job.id}">Edit</button>
                    <button class="btn btn-small btn-secondary" type="button" data-action="preview" data-id="${job.id}">Preview</button>
                    <button class="btn-link" type="button" data-action="applications" data-id="${job.id}">${job.applications_count} application${job.applications_count === 1 ? "" : "s"}</button>
                    ${job.applications_count === 0 ? `<button class="btn-link danger" type="button" data-action="delete" data-id="${job.id}">Delete</button>` : ""}
                </div>
            </article>`;
        }).join("");
    }

    ["job-search", "job-status-filter", "job-business-filter"].forEach(id => {
        $(id).addEventListener("input", renderJobs);
    });

    $("jobs-list").addEventListener("click", async event => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        const action = button.dataset.action;
        const job = state.jobs.find(j => String(j.id) === button.dataset.id);

        if (action === "new") {
            resetJobForm();
            showTab("post");
            return;
        }
        if (!job) return;

        if (action === "edit") {
            fillJobForm(job);
            showTab("post");
            window.scrollTo({ top: 0, behavior: "smooth" });
        } else if (action === "preview") {
            showJobPreview(job);
        } else if (action === "applications") {
            $("app-job-filter").value = String(job.id);
            renderApplications();
            showTab("applications");
        } else if (action === "status") {
            const status = button.dataset.status;
            if (status === "closed") {
                const ok = await confirmAction({
                    title: "Close this job?",
                    text: "Job seekers will no longer see it or be able to apply. You can reopen it later.",
                    confirmLabel: "Close job",
                    danger: true,
                });
                if (!ok) return;
            }
            await withButton(button, "Saving…", async () => {
                try {
                    const result = await api(`/api/company/jobs/${job.id}/status`, { method: "PATCH", data: { status } });
                    toast(result.message);
                    await Promise.all([loadOverview(), loadJobs()]);
                } catch (error) {
                    fail(error);
                }
            });
        } else if (action === "delete") {
            const ok = await confirmAction({
                title: "Delete this job?",
                text: `"${job.title}" will be removed permanently.`,
                confirmLabel: "Delete job",
                danger: true,
            });
            if (!ok) return;
            try {
                const result = await api(`/api/company/jobs/${job.id}`, { method: "DELETE" });
                toast(result.message);
                await Promise.all([loadOverview(), loadJobs()]);
            } catch (error) {
                fail(error);
            }
        }
    });

    function showJobPreview(job) {
        const contact = job.company;
        $("job-modal-body").innerHTML = `
            <p class="eyebrow">Preview · how job seekers see it</p>
            <h2 id="job-modal-title">${escapeHtml(job.title)}</h2>
            <div class="item-meta">
                <span>${escapeHtml(contact.name)}</span>
                ${job.job_type ? `<span>${escapeHtml(job.job_type)}</span>` : ""}
                ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ""}
                ${badge(job.status)}
            </div>
            ${job.status !== "published" ? `<div class="notice info section-gap">This job is ${escapeHtml(job.status)}. Job seekers will only see it once it is published.</div>` : ""}
            <div class="detail-section"><h3>Work description</h3><p class="item-text pre-line">${escapeHtml(job.description)}</p></div>
            <div class="detail-section"><h3>Requirements</h3><p class="item-text pre-line">${escapeHtml(job.requirements)}</p></div>
            <div class="detail-section"><h3>Contact</h3>
                <div class="contact-list">
                    <span>✉ ${escapeHtml(contact.email)}</span>
                    ${contact.phone ? `<span>☎ ${escapeHtml(contact.phone)}</span>` : ""}
                    ${contact.alt_phone ? `<span>☎ ${escapeHtml(contact.alt_phone)}</span>` : ""}
                </div>
            </div>`;
        openModal("job-modal");
    }

    // ---------------------------------------------------------
    // Post / edit job form
    // ---------------------------------------------------------

    function resetJobForm() {
        $("job-form").reset();
        $("job_id").value = "";
        $("job-form-title").textContent = "Post a new job";
        $("job-form-subtitle").textContent = "Describe the work and what a candidate needs. You can save it as a draft first.";
        $("job-publish-btn").textContent = "Publish job";
        $("job-draft-btn").textContent = "Save as draft";
        $("job-cancel-btn").hidden = true;
        $("job-form-error").classList.remove("show");
        const first = $("job-business").options[0];
        if (first) $("job-business").value = first.value;
    }

    function fillJobForm(job) {
        $("job_id").value = job.id;
        $("job-title").value = job.title;
        $("job-business").value = job.business.id;
        $("job-type").value = job.job_type || "";
        $("job-location").value = job.location || "";
        $("job-description").value = job.description;
        $("job-requirements").value = job.requirements;
        $("job-form-title").textContent = `Edit: ${job.title}`;
        $("job-form-subtitle").textContent = `Current status: ${job.status}. Choose how to save your changes.`;
        $("job-publish-btn").textContent = job.status === "published" ? "Save changes" : "Save & publish";
        $("job-draft-btn").textContent = job.status === "draft" ? "Save changes" : "Save as draft";
        $("job-cancel-btn").hidden = false;
        $("job-form-error").classList.remove("show");
    }

    // "+ Post a job" buttons always start a fresh job
    document.querySelectorAll('[data-go="post"]').forEach(button => button.addEventListener("click", resetJobForm));

    $("job-cancel-btn").addEventListener("click", () => {
        resetJobForm();
        showTab("jobs");
    });

    $("job-form").addEventListener("submit", async event => {
        event.preventDefault();
        const form = event.target;
        const button = event.submitter || $("job-publish-btn");
        const status = button.dataset.status || "published";
        const errorBox = $("job-form-error");
        errorBox.classList.remove("show");

        // Friendly checks before sending (the backend checks again)
        const missing = [
            ["job-title", "a job title"],
            ["job-description", "a work description"],
            ["job-requirements", "the requirements"],
        ].filter(([id]) => !$(id).value.trim()).map(([, label]) => label);
        if (missing.length) {
            errorBox.textContent = `Please add ${missing.join(", ")}.`;
            errorBox.classList.add("show");
            $(["job-title", "job-description", "job-requirements"].find(id => !$(id).value.trim())).focus();
            return;
        }

        const data = new FormData(form);
        data.set("status", status);
        const jobId = data.get("job_id");
        data.delete("job_id");

        await withButton(button, "Saving…", async () => {
            try {
                const result = jobId
                    ? await api(`/api/company/jobs/${jobId}`, { method: "PUT", data })
                    : await api("/api/company/jobs", { method: "POST", data });
                toast(result.message);
                resetJobForm();
                await Promise.all([loadOverview(), loadJobs()]);
                $("job-status-filter").value = "";
                renderJobs();
                showTab("jobs");
            } catch (error) {
                if (error.status === 401) return fail(error);
                errorBox.textContent = error.message;
                errorBox.classList.add("show");
            }
        });
    });

    // ---------------------------------------------------------
    // Applications
    // ---------------------------------------------------------

    function renderJobFilterForApplications() {
        const select = $("app-job-filter");
        const current = select.value;
        select.innerHTML = `<option value="">All jobs</option>` + state.jobs.map(j => `<option value="${j.id}">${escapeHtml(j.title)}</option>`).join("");
        select.value = current;
    }

    function renderApplications() {
        const jobId = $("app-job-filter").value;
        const status = $("app-status-filter").value;
        const search = $("app-search").value.trim().toLowerCase();
        const statuses = state.overview ? state.overview.application_statuses : ["pending", "reviewed", "shortlisted", "rejected", "accepted"];

        const apps = state.applications.filter(app =>
            (!jobId || String(app.job.id) === jobId) &&
            (!status || app.status === status) &&
            (!search || `${app.applicant.full_name} ${app.applicant.email} ${app.applicant.phone}`.toLowerCase().includes(search))
        );

        if (!state.applications.length) {
            $("applications-list").innerHTML = `
                <div class="empty">
                    <strong>No applications yet</strong>
                    When job seekers apply for your published jobs, they will show up here.
                </div>`;
            return;
        }
        if (!apps.length) {
            $("applications-list").innerHTML = `<div class="empty"><strong>No applications match your filters</strong>Try another job or status.</div>`;
            return;
        }

        $("applications-list").innerHTML = apps.map(app => {
            const a = app.applicant;
            const skills = a.skills.length
                ? `<div class="chips">${a.skills.map(s => `<span class="chip ${s.status === "Completed" ? "match" : ""}">${escapeHtml(s.name)} · ${s.display_percentage ?? 0}%</span>`).join("")}</div>`
                : `<span class="small muted">No skills tracked on OpenLane yet.</span>`;
            return `
            <article class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(a.full_name)}</div>
                        <div class="item-meta">
                            <span>Applied for <strong>${escapeHtml(app.job.title)}</strong></span>
                            <span>${formatDate(app.created_at)}</span>
                            ${a.location ? `<span>📍 ${escapeHtml(a.location)}</span>` : ""}
                        </div>
                    </div>
                    <label class="actions">
                        <span class="sr-only" style="position:absolute;left:-9999px">Application status</span>
                        <select class="select-inline" data-app-status="${app.id}" aria-label="Status for ${escapeHtml(a.full_name)}">
                            ${statuses.map(s => `<option value="${s}" ${s === app.status ? "selected" : ""}>${s[0].toUpperCase() + s.slice(1)}</option>`).join("")}
                        </select>
                    </label>
                </div>
                ${app.message ? `<p class="item-text pre-line">“${escapeHtml(app.message)}”</p>` : ""}
                ${a.bio ? `<p class="item-text small muted">${escapeHtml(a.bio)}</p>` : ""}
                <div>
                    <p class="small muted" style="margin-bottom:6px">Skills progress on OpenLane${a.overall !== null && a.overall !== undefined ? ` · average ${a.overall}%` : ""}</p>
                    ${skills}
                </div>
                <div class="actions">
                    ${a.email ? `<a class="btn btn-small btn-secondary" href="mailto:${escapeHtml(a.email)}?subject=${encodeURIComponent("Your application: " + app.job.title)}">✉ ${escapeHtml(a.email)}</a>` : ""}
                    ${a.phone ? `<a class="btn btn-small btn-secondary" href="tel:${escapeHtml(a.phone)}">☎ ${escapeHtml(a.phone)}</a>` : ""}
                    ${a.portfolio_url ? `<a class="btn btn-small btn-secondary" href="${escapeHtml(a.portfolio_url)}" target="_blank" rel="noopener noreferrer">Portfolio ↗</a>` : ""}
                </div>
            </article>`;
        }).join("");
    }

    ["app-job-filter", "app-status-filter", "app-search"].forEach(id => $(id).addEventListener("input", renderApplications));

    $("applications-list").addEventListener("change", async event => {
        const select = event.target.closest("[data-app-status]");
        if (!select) return;
        const id = select.dataset.appStatus;
        const app = state.applications.find(a => String(a.id) === id);
        const previous = app ? app.status : "";
        select.disabled = true;
        try {
            const result = await api(`/api/company/applications/${id}/status`, { method: "PATCH", data: { status: select.value } });
            if (app) app.status = result.status;
            toast(result.message);
            await loadOverview();
            renderRecentApplications();
        } catch (error) {
            select.value = previous;
            fail(error);
        } finally {
            select.disabled = false;
        }
    });

    // ---------------------------------------------------------
    // Company profile and businesses
    // ---------------------------------------------------------

    function fillProfileForm(company) {
        const form = $("profile-form");
        if (form.dataset.dirty === "true") return;
        $("p-company-name").value = company.company_name;
        $("p-email").value = company.email;
        $("p-phone").value = company.phone;
        $("p-alt-phone").value = company.alt_phone;
        $("p-description").value = company.description;
    }

    $("profile-form").addEventListener("input", () => { $("profile-form").dataset.dirty = "true"; });

    $("profile-form").addEventListener("submit", async event => {
        event.preventDefault();
        const form = event.target;
        const errorBox = $("profile-error");
        errorBox.classList.remove("show");
        await withButton(form.querySelector("button[type=submit]"), "Saving…", async () => {
            try {
                const result = await api("/api/company/profile", { method: "PUT", data: new FormData(form) });
                form.dataset.dirty = "false";
                toast(result.message);
                await loadOverview();
                renderGettingStarted();
            } catch (error) {
                if (error.status === 401) return fail(error);
                errorBox.textContent = error.message;
                errorBox.classList.add("show");
            }
        });
    });

    function renderBusinesses(businesses) {
        $("business-list").innerHTML = businesses.map(b => `
            <div class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(b.name)}</div>
                        <div class="item-meta">${b.description ? `<span>${escapeHtml(b.description)}</span>` : ""}<span>${b.jobs_count} job${b.jobs_count === 1 ? "" : "s"}</span></div>
                    </div>
                    <div class="actions">
                        <button class="btn-link" type="button" data-business-edit="${b.id}">Edit</button>
                        ${b.jobs_count === 0 && businesses.length > 1 ? `<button class="btn-link danger" type="button" data-business-delete="${b.id}">Remove</button>` : ""}
                    </div>
                </div>
            </div>`).join("") || `<div class="empty">No businesses yet.</div>`;
    }

    function resetBusinessForm() {
        $("business-form").reset();
        $("business_id").value = "";
        $("b-name-label").textContent = "Add a business or branch";
        $("business-submit").textContent = "Add business";
        $("business-cancel").hidden = true;
    }

    $("business-cancel").addEventListener("click", resetBusinessForm);

    $("business-list").addEventListener("click", async event => {
        const edit = event.target.closest("[data-business-edit]");
        const remove = event.target.closest("[data-business-delete]");
        const businesses = state.overview.businesses;
        if (edit) {
            const b = businesses.find(x => String(x.id) === edit.dataset.businessEdit);
            $("business_id").value = b.id;
            $("b-name").value = b.name;
            $("b-description").value = b.description;
            $("b-name-label").textContent = "Edit business name";
            $("business-submit").textContent = "Save business";
            $("business-cancel").hidden = false;
            $("b-name").focus();
        }
        if (remove) {
            const b = businesses.find(x => String(x.id) === remove.dataset.businessDelete);
            const ok = await confirmAction({ title: "Remove this business?", text: `"${b.name}" will be removed.`, confirmLabel: "Remove", danger: true });
            if (!ok) return;
            try {
                const result = await api(`/api/company/businesses/${b.id}`, { method: "DELETE" });
                toast(result.message);
                await loadOverview();
            } catch (error) {
                fail(error);
            }
        }
    });

    $("business-form").addEventListener("submit", async event => {
        event.preventDefault();
        const form = event.target;
        if (!$("b-name").value.trim()) {
            toast("Please enter a business name", "error");
            $("b-name").focus();
            return;
        }
        const id = $("business_id").value;
        const data = new FormData(form);
        data.delete("business_id");
        await withButton($("business-submit"), "Saving…", async () => {
            try {
                const result = id
                    ? await api(`/api/company/businesses/${id}`, { method: "PUT", data })
                    : await api("/api/company/businesses", { method: "POST", data });
                toast(result.message);
                resetBusinessForm();
                await Promise.all([loadOverview(), loadJobs()]);
            } catch (error) {
                fail(error);
            }
        });
    });

    refreshAll();
});
