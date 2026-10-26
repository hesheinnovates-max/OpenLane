// =========================================================
// Job seeker dashboard: learning progress, skills, jobs,
// applications and profile
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    const { api, toast, escapeHtml, badge, formatDate, timeAgo, progressBar, withButton, handleError, confirmAction, openModal, closeModal } = OpenLane;
    const LOGIN = "/job-seeker/login";

    const state = {
        me: null,
        learning: { skills: [], overall: null },
        catalogue: [],
        jobs: [],
        applications: [],
        openSkillId: null,
    };

    const $ = id => document.getElementById(id);
    const fail = error => handleError(error, LOGIN);
    const GROUPS = ["In Progress", "Not Started", "Completed"];

    OpenLane.setupTabs(name => {
        if (name === "jobs" && !state.jobsLoaded) loadJobs();
    });

    // ---------------------------------------------------------
    // Loading
    // ---------------------------------------------------------

    async function loadMe() {
        state.me = await api("/api/me");
        const firstName = (state.me.name || "").split(" ")[0] || "there";
        $("top-name").textContent = state.me.name;
        $("welcome").textContent = `Hi ${firstName} 👋`;
    }

    async function loadLearning() {
        state.learning = await api("/api/job-seeker/skills");
        renderLearning();
    }

    async function loadCatalogue() {
        state.catalogue = await api("/api/skills");
        renderCategories();
        renderCatalogue();
    }

    async function loadJobs() {
        try {
            const result = await api(OpenLaneJobs.jobsQuery(
                $("job-search").value.trim(),
                $("job-type-filter").value,
                $("job-location-filter").value.trim()
            ));
            state.jobs = result.jobs;
            state.jobsLoaded = true;
            OpenLaneJobs.fillJobTypes($("job-type-filter"), result.job_types);
            renderJobs();
        } catch (error) {
            fail(error);
        }
    }

    async function loadApplications() {
        state.applications = await api("/api/job-seeker/applications");
        renderApplications();
    }

    async function loadProfile() {
        const profile = await api("/api/job-seeker/profile");
        $("p-full-name").value = profile.full_name;
        $("p-email").value = profile.email;
        $("p-phone").value = profile.phone;
        $("p-location").value = profile.location;
        $("p-portfolio").value = profile.portfolio_url;
        $("p-bio").value = profile.bio;
    }

    async function start() {
        try {
            await loadMe();
            await Promise.all([loadLearning(), loadCatalogue(), loadApplications(), loadProfile()]);
            if (location.hash === "#jobs") loadJobs();
        } catch (error) {
            fail(error);
        }
    }

    // ---------------------------------------------------------
    // My learning
    // ---------------------------------------------------------

    function renderLearning() {
        const { skills, overall } = state.learning;
        $("count-skills").textContent = skills.length;

        if (overall.display_percentage === null || overall.display_percentage === undefined) {
            $("overall-number").textContent = "–";
            $("overall-bar").innerHTML = `<p class="small muted">Add a skill to start tracking your progress.</p>`;
        } else {
            $("overall-number").textContent = `${overall.display_percentage}%`;
            $("overall-bar").innerHTML = progressBar(overall.display_percentage, { big: true, label: "Overall progress" });
        }
        $("overall-formula").textContent = `${overall.formula} (${overall.total} skill${overall.total === 1 ? "" : "s"})`;
        $("overall-legend").innerHTML = GROUPS.map(g => `<span class="badge ${g.toLowerCase().replace(" ", "-")}">${overall.counts[g] || 0} ${g}</span>`).join("");

        renderNextStep();

        if (!skills.length) {
            $("my-skills").innerHTML = `
                <div class="empty">
                    <strong>You have not selected any skills yet</strong>
                    Browse the skill catalogue and add the skills you want to learn.
                    <div><button class="btn btn-inline" type="button" data-open-tab="catalogue">Browse skills</button></div>
                </div>`;
            return;
        }

        $("my-skills").innerHTML = GROUPS.map(group => {
            const items = skills.filter(s => s.status === group);
            return `
                <h3 class="group-title">${badge(group)} <span class="muted small">${items.length} skill${items.length === 1 ? "" : "s"}</span></h3>
                ${items.length ? `<div class="grid-cards">${items.map(skillProgressCard).join("")}</div>`
                    : `<div class="empty" style="padding:18px">${{
                        "In Progress": "Nothing in progress. Start one of your skills below.",
                        "Not Started": "No skills waiting to be started.",
                        "Completed": "No completed skills yet. Keep going!",
                    }[group]}</div>`}`;
        }).join("");
    }

    function skillProgressCard(skill) {
        const action = skill.status === "Not Started" ? "Start" : skill.status === "Completed" ? "Review" : "Continue";
        return `
            <article class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(skill.name)}</div>
                        <div class="item-meta"><span>${escapeHtml(skill.category)}</span><span>${skill.completed_steps} of ${skill.total_steps} steps</span></div>
                    </div>
                </div>
                ${progressBar(skill.display_percentage, { label: `${skill.name} progress` })}
                <div class="actions">
                    <button class="btn btn-small ${skill.status === "Completed" ? "btn-secondary" : ""}" type="button" data-skill-open="${skill.id}" data-skill-start="${skill.status === "Not Started" ? "1" : ""}">${action}</button>
                    <button class="btn-link" type="button" data-skill-open="${skill.id}">View steps</button>
                </div>
            </article>`;
    }

    function renderNextStep() {
        const skills = state.learning.skills;
        const current = skills.find(s => s.status === "In Progress") || skills.find(s => s.status === "Not Started");
        if (!current) {
            $("next-step").innerHTML = skills.length
                ? `<div class="empty" style="padding:20px"><strong>All your skills are complete 🎉</strong>Add a new skill or look for jobs that match.<div class="form-actions" style="justify-content:center"><button class="btn btn-inline" type="button" data-open-tab="jobs">Find jobs</button></div></div>`
                : `<div class="empty" style="padding:20px"><strong>Start with a skill</strong>Pick something from the catalogue to begin.<div><button class="btn btn-inline" type="button" data-open-tab="catalogue">Browse skills</button></div></div>`;
            return;
        }
        const next = (current.steps || []).find(step => !step.completed);
        $("next-step").innerHTML = `
            <div class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(current.name)}</div>
                        <div class="item-meta"><span>${current.completed_steps} of ${current.total_steps} steps done</span></div>
                    </div>
                    ${badge(current.status)}
                </div>
                ${progressBar(current.display_percentage, { label: `${current.name} progress` })}
                ${next ? `<p class="item-text"><strong>Next:</strong> ${escapeHtml(next.title)}</p>` : ""}
                <button class="btn btn-small" type="button" data-skill-open="${current.id}" data-skill-start="${current.status === "Not Started" ? "1" : ""}">${current.status === "Not Started" ? "Start this skill" : "Continue"}</button>
            </div>`;
    }

    // Buttons that open another tab
    document.addEventListener("click", event => {
        const tabButton = event.target.closest("[data-open-tab]");
        if (tabButton) {
            document.querySelector(`[data-tab="${tabButton.dataset.openTab}"]`)?.click();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    });

    // Open a selected skill (and start it if asked)
    document.addEventListener("click", async event => {
        const button = event.target.closest("[data-skill-open]");
        if (!button) return;
        const id = Number(button.dataset.skillOpen);
        if (button.dataset.skillStart === "1") {
            await withButton(button, "Starting…", async () => {
                try {
                    const result = await api(`/api/job-seeker/skills/${id}/start`, { method: "POST" });
                    updateSkill(result);
                    toast(result.message);
                } catch (error) {
                    fail(error);
                }
            });
        }
        openSkill(id);
    });

    function updateSkill(result) {
        const index = state.learning.skills.findIndex(s => s.id === result.skill.id);
        if (index >= 0) state.learning.skills[index] = result.skill;
        else state.learning.skills.push(result.skill);
        state.learning.overall = result.overall;
        renderLearning();
        if (state.openSkillId === result.skill.id) renderSkillModal(result.skill);
    }

    function openSkill(id) {
        const skill = state.learning.skills.find(s => s.id === id);
        if (!skill) return;
        state.openSkillId = id;
        renderSkillModal(skill);
        openModal("skill-modal");
    }

    function renderSkillModal(skill) {
        $("skill-modal-body").innerHTML = `
            <p class="eyebrow">${escapeHtml(skill.category || "Skill")}</p>
            <h2 id="skill-modal-title">${escapeHtml(skill.name)}</h2>
            <div class="item-meta" style="margin-bottom:14px">${badge(skill.status)}<span>${skill.completed_steps} of ${skill.total_steps} required steps complete</span></div>
            ${progressBar(skill.display_percentage, { big: true, label: `${skill.name} progress` })}
            <p class="item-text section-gap">${escapeHtml(skill.description)}</p>
            <div class="detail-section">
                <h3>Learning steps</h3>
                ${skill.steps.length ? `
                <div class="steps" id="step-list">
                    ${skill.steps.map((step, index) => `
                        <label class="step ${step.completed ? "done" : ""}">
                            <input type="checkbox" data-step="${step.id}" ${step.completed ? "checked" : ""}>
                            <div>
                                <strong>${index + 1}. ${escapeHtml(step.title)}</strong>
                                ${step.description ? `<span>${escapeHtml(step.description)}</span>` : ""}
                            </div>
                        </label>`).join("")}
                </div>` : `<div class="empty">This skill has no learning steps yet, so progress is unavailable. The OpenLane team will add them soon.</div>`}
            </div>
            <p class="small muted section-gap">Tick a step when you have completed it. Your percentage is worked out from these steps.</p>
            <div class="form-actions section-gap">
                ${skill.status === "Not Started" ? `<button class="btn btn-inline" type="button" id="modal-start">Start this skill</button>` : ""}
                <button class="btn btn-inline btn-secondary" type="button" id="modal-remove">Remove from my list</button>
            </div>`;

        $("modal-start")?.addEventListener("click", async event => {
            await withButton(event.target, "Starting…", async () => {
                try {
                    const result = await api(`/api/job-seeker/skills/${skill.id}/start`, { method: "POST" });
                    updateSkill(result);
                    toast(result.message);
                } catch (error) {
                    fail(error);
                }
            });
        });

        $("modal-remove").addEventListener("click", async () => {
            const ok = await confirmAction({
                title: `Remove ${skill.name}?`,
                text: "Your progress on this skill will be deleted. You can add it again later, but you will start from 0%.",
                confirmLabel: "Remove skill",
                danger: true,
            });
            if (!ok) {
                openModal("skill-modal");
                return;
            }
            try {
                const result = await api(`/api/job-seeker/skills/${skill.id}`, { method: "DELETE" });
                toast(result.message);
                closeModal("skill-modal");
                state.openSkillId = null;
                await Promise.all([loadLearning(), loadCatalogue()]);
            } catch (error) {
                fail(error);
            }
        });
    }

    // Tick / untick a learning step , the backend saves it and returns the new percentage
    $("skill-modal-body").addEventListener("change", async event => {
        const box = event.target.closest("[data-step]");
        if (!box) return;
        const skillId = state.openSkillId;
        const completed = box.checked;
        document.querySelectorAll("#step-list input").forEach(input => { input.disabled = true; });
        try {
            const result = await api(`/api/job-seeker/skills/${skillId}/steps/${box.dataset.step}`, {
                method: "PATCH",
                data: { completed: completed ? "true" : "false" },
            });
            updateSkill(result);
            toast(result.message);
        } catch (error) {
            // Do not pretend it saved: put the checkbox back
            box.checked = !completed;
            document.querySelectorAll("#step-list input").forEach(input => { input.disabled = false; });
            fail(error);
        }
    });

    // ---------------------------------------------------------
    // Catalogue
    // ---------------------------------------------------------

    function renderCategories() {
        const select = $("skill-category");
        const current = select.value;
        const categories = [...new Set(state.catalogue.map(s => s.category).filter(Boolean))];
        select.innerHTML = `<option value="">All categories</option>` + categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
        select.value = current;
    }

    function renderCatalogue() {
        const search = $("skill-search").value.trim().toLowerCase();
        const category = $("skill-category").value;
        const skills = state.catalogue.filter(s =>
            (!category || s.category === category) &&
            (!search || `${s.name} ${s.description} ${s.category}`.toLowerCase().includes(search))
        );
        if (!skills.length) {
            $("catalogue").innerHTML = `<div class="empty" style="grid-column:1/-1"><strong>No skills found</strong>Try another search word.</div>`;
            return;
        }
        $("catalogue").innerHTML = skills.map(skill => `
            <article class="item">
                <div>
                    <span class="chip">${escapeHtml(skill.category || "General")}</span>
                </div>
                <div class="item-title">${escapeHtml(skill.name)}</div>
                <p class="item-text">${escapeHtml(skill.description)}</p>
                <div class="item-meta"><span>${skill.steps_count} learning step${skill.steps_count === 1 ? "" : "s"}</span></div>
                <div class="actions">
                    ${skill.selected
                        ? `<span class="badge completed">In your list</span>`
                        : `<button class="btn btn-small" type="button" data-add-skill="${skill.id}">+ Add to my list</button>`}
                    <button class="btn-link" type="button" data-preview-skill="${skill.id}">View steps</button>
                </div>
            </article>`).join("");
    }

    ["skill-search", "skill-category"].forEach(id => $(id).addEventListener("input", renderCatalogue));

    $("catalogue").addEventListener("click", async event => {
        const add = event.target.closest("[data-add-skill]");
        const preview = event.target.closest("[data-preview-skill]");
        if (add) {
            await addSkill(Number(add.dataset.addSkill), add);
        }
        if (preview) {
            const skill = state.catalogue.find(s => s.id === Number(preview.dataset.previewSkill));
            $("skill-modal-body").innerHTML = `
                <p class="eyebrow">${escapeHtml(skill.category || "Skill")}</p>
                <h2 id="skill-modal-title">${escapeHtml(skill.name)}</h2>
                <p class="item-text">${escapeHtml(skill.description)}</p>
                <div class="detail-section">
                    <h3>What you need to complete</h3>
                    <ol class="steps" style="list-style:none">
                        ${skill.steps.map((step, i) => `<li class="step" style="cursor:default"><div><strong>${i + 1}. ${escapeHtml(step.title)}</strong>${step.description ? `<span>${escapeHtml(step.description)}</span>` : ""}</div></li>`).join("")}
                    </ol>
                </div>
                <div class="form-actions section-gap">
                    ${skill.selected ? `<span class="badge completed">Already in your list</span>` : `<button class="btn btn-inline" type="button" id="modal-add-skill">+ Add to my list</button>`}
                </div>`;
            state.openSkillId = null;
            openModal("skill-modal");
            $("modal-add-skill")?.addEventListener("click", async e => {
                await addSkill(skill.id, e.target);
                closeModal("skill-modal");
            });
        }
    });

    async function addSkill(id, button) {
        await withButton(button, "Adding…", async () => {
            try {
                const result = await api("/api/job-seeker/skills", { method: "POST", data: { skill_id: id } });
                toast(result.message);
                const skill = state.catalogue.find(s => s.id === id);
                if (skill) skill.selected = true;
                state.learning.skills.push(result.skill);
                state.learning.overall = result.overall;
                renderLearning();
                renderCatalogue();
            } catch (error) {
                fail(error);
            }
        });
    }

    // ---------------------------------------------------------
    // Jobs
    // ---------------------------------------------------------

    function renderJobs() {
        if (!state.jobs.length) {
            const filtered = $("job-search").value || $("job-type-filter").value || $("job-location-filter").value;
            $("jobs-list").innerHTML = `<div class="empty"><strong>${filtered ? "No jobs match your search" : "No jobs published yet"}</strong>${filtered ? "Try different words or clear the filters." : "Check back soon, companies are adding opportunities."}</div>`;
            return;
        }
        $("jobs-list").innerHTML = state.jobs.map(job => OpenLaneJobs.jobCard(job, state.learning.skills)).join("");
    }

    let searchTimer;
    ["job-search", "job-type-filter", "job-location-filter"].forEach(id => {
        $(id).addEventListener("input", () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(loadJobs, 300);
        });
    });

    $("jobs-list").addEventListener("click", event => {
        const card = event.target.closest("[data-job-id]");
        if (!card) return;
        const job = state.jobs.find(j => String(j.id) === card.dataset.jobId);
        if (job) showJob(job);
    });

    function showJob(job) {
        const body = $("job-modal-body");
        body.innerHTML = OpenLaneJobs.jobDetail(job, { skills: state.learning.skills, isJobSeeker: true });
        OpenLaneJobs.bindApply(body, job, async applied => {
            showJob(applied);
            renderJobs();
            await loadApplications();
        });
        openModal("job-modal");
    }

    // ---------------------------------------------------------
    // Applications
    // ---------------------------------------------------------

    const STATUS_HELP = {
        pending: "Sent, waiting for the company to look at it.",
        reviewed: "The company has looked at your application.",
        shortlisted: "Good news, you are on the shortlist. The company may contact you.",
        rejected: "The company did not continue with your application this time.",
        accepted: "Congratulations! The company accepted your application.",
    };

    function renderApplications() {
        $("count-applications").textContent = state.applications.length;
        if (!state.applications.length) {
            $("applications-list").innerHTML = `
                <div class="empty">
                    <strong>You have not applied for any jobs yet</strong>
                    Find a job that fits your skills and apply from the job details.
                    <div><button class="btn btn-inline" type="button" data-open-tab="jobs">Find jobs</button></div>
                </div>`;
            return;
        }
        $("applications-list").innerHTML = state.applications.map(app => `
            <article class="item">
                <div class="item-top">
                    <div>
                        <div class="item-title">${escapeHtml(app.job.title)}</div>
                        <div class="item-meta">
                            <span><strong>${escapeHtml(app.job.company.name)}</strong></span>
                            ${app.job.location ? `<span>📍 ${escapeHtml(app.job.location)}</span>` : ""}
                            <span>Applied ${formatDate(app.created_at)}</span>
                        </div>
                    </div>
                    ${badge(app.status)}
                </div>
                <p class="small muted">${escapeHtml(STATUS_HELP[app.status] || "")}${app.job.status !== "published" ? " This job is no longer open." : ""}</p>
                <div class="actions">
                    ${app.job.company.email ? `<a class="btn btn-small btn-secondary" href="mailto:${escapeHtml(app.job.company.email)}">✉ Contact company</a>` : ""}
                    ${["pending", "reviewed"].includes(app.status) ? `<button class="btn-link danger" type="button" data-withdraw="${app.id}">Withdraw</button>` : ""}
                </div>
            </article>`).join("");
    }

    $("applications-list").addEventListener("click", async event => {
        const button = event.target.closest("[data-withdraw]");
        if (!button) return;
        const ok = await confirmAction({ title: "Withdraw this application?", text: "The company will no longer see your application.", confirmLabel: "Withdraw", danger: true });
        if (!ok) return;
        try {
            const result = await api(`/api/job-seeker/applications/${button.dataset.withdraw}`, { method: "DELETE" });
            toast(result.message);
            await loadApplications();
            if (state.jobsLoaded) loadJobs();
        } catch (error) {
            fail(error);
        }
    });

    // ---------------------------------------------------------
    // Profile
    // ---------------------------------------------------------

    $("profile-form").addEventListener("submit", async event => {
        event.preventDefault();
        const form = event.target;
        const errorBox = $("profile-error");
        errorBox.classList.remove("show");
        if (!$("p-email").value.trim() && !$("p-phone").value.trim()) {
            errorBox.textContent = "Please keep an email address or a phone number.";
            errorBox.classList.add("show");
            return;
        }
        await withButton(form.querySelector("button[type=submit]"), "Saving…", async () => {
            try {
                const result = await api("/api/job-seeker/profile", { method: "PUT", data: new FormData(form) });
                toast(result.message);
                await loadMe();
            } catch (error) {
                if (error.status === 401) return fail(error);
                errorBox.textContent = error.message;
                errorBox.classList.add("show");
            }
        });
    });

    start();
});
