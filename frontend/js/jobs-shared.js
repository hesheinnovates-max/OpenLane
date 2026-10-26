// =========================================================
// Job listing pieces shared by the public jobs page
// and the job seeker dashboard
// =========================================================

const OpenLaneJobs = (() => {
    const { escapeHtml, badge, timeAgo, api, toast, withButton } = OpenLane;

    // Words we look for in a job's text for each skill, e.g.
    // "Spreadsheets (Excel / Google Sheets)" -> ["spreadsheets", "excel", "google sheets"]
    function skillKeywords(name) {
        const keywords = [];
        const main = name.replace(/\(.*\)/, "").trim();
        if (main) keywords.push(main);
        const inside = name.match(/\(([^)]*)\)/);
        if (inside) inside[1].split("/").forEach(part => part.trim() && keywords.push(part.trim()));
        main.split(/\s*[&/]\s*/).forEach(part => part.trim() && part !== main && keywords.push(part.trim()));
        return keywords.map(k => k.toLowerCase()).filter(k => k.length > 2);
    }

    function matchingSkills(job, skills) {
        const text = `${job.title} ${job.requirements} ${job.description}`.toLowerCase();
        return (skills || []).filter(skill => skillKeywords(skill.name).some(word => text.includes(word)));
    }

    function jobCard(job, skills) {
        const matches = matchingSkills(job, skills);
        return `
        <button class="item" type="button" data-job-id="${job.id}" aria-label="Open ${escapeHtml(job.title)}">
            <div class="item-top">
                <div>
                    <div class="item-title">${escapeHtml(job.title)}</div>
                    <div class="item-meta">
                        <span><strong>${escapeHtml(job.company.name)}</strong></span>
                        ${job.job_type ? `<span>${escapeHtml(job.job_type)}</span>` : ""}
                        ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ""}
                        <span>${timeAgo(job.created_at)}</span>
                    </div>
                </div>
                ${job.applied ? `<span class="badge completed">Applied</span>` : ""}
            </div>
            <p class="item-text clamp">${escapeHtml(job.description)}</p>
            ${matches.length ? `<div class="chips">${matches.map(s => `<span class="chip match">✓ ${escapeHtml(s.name)}</span>`).join("")}</div>` : ""}
        </button>`;
    }

    function jobDetail(job, { skills = [], isJobSeeker = false } = {}) {
        const matches = matchingSkills(job, skills);
        const c = job.company;
        let applyBlock;
        if (job.applied) {
            applyBlock = `<div class="notice success show">You applied for this job. Follow it under <strong>My applications</strong>.</div>`;
        } else if (isJobSeeker) {
            applyBlock = `
                <form class="form" id="apply-form" style="margin-top:0">
                    <div class="form-group">
                        <label for="apply-message">Message to the company <span class="field-hint">(optional)</span></label>
                        <textarea id="apply-message" name="message" maxlength="2000" rows="4" placeholder="Say why you are a good fit and when you are available."></textarea>
                    </div>
                    <button class="btn" type="submit">Apply for this job</button>
                </form>`;
        } else {
            applyBlock = `
                <div class="notice info">Log in as a Job Seeker to apply inside OpenLane, or use the contact details above.</div>
                <div class="form-actions" style="margin-top:12px">
                    <a class="btn btn-inline" href="/job-seeker/login" style="display:inline-grid;place-items:center">Log in to apply</a>
                    <a class="btn btn-inline btn-secondary" href="/job-seeker/register" style="display:inline-grid;place-items:center">Create an account</a>
                </div>`;
        }

        return `
            <p class="eyebrow">${escapeHtml(c.name)}</p>
            <h2 id="job-modal-title">${escapeHtml(job.title)}</h2>
            <div class="item-meta">
                ${job.job_type ? `<span>${escapeHtml(job.job_type)}</span>` : ""}
                ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ""}
                <span>Posted ${timeAgo(job.created_at)}</span>
            </div>
            ${isJobSeeker ? `
            <div class="detail-section">
                <h3>Your matching skills</h3>
                ${matches.length
                    ? `<div class="chips">${matches.map(s => `<span class="chip match">✓ ${escapeHtml(s.name)} · ${s.display_percentage ?? 0}%</span>`).join("")}</div>`
                    : `<p class="small muted">None of your selected skills are named in this listing. Read the requirements below to compare.</p>`}
            </div>` : ""}
            <div class="detail-section"><h3>Work description</h3><p class="item-text pre-line">${escapeHtml(job.description)}</p></div>
            <div class="detail-section"><h3>Requirements</h3><p class="item-text pre-line">${escapeHtml(job.requirements)}</p></div>
            ${c.description ? `<div class="detail-section"><h3>About ${escapeHtml(c.name)}</h3><p class="item-text">${escapeHtml(c.description)}</p></div>` : ""}
            <div class="detail-section"><h3>Contact</h3>
                <div class="contact-list">
                    ${c.email ? `<a href="mailto:${escapeHtml(c.email)}?subject=${encodeURIComponent(job.title)}">✉ ${escapeHtml(c.email)}</a>` : ""}
                    ${c.phone ? `<a href="tel:${escapeHtml(c.phone)}">☎ ${escapeHtml(c.phone)}</a>` : ""}
                    ${c.alt_phone ? `<a href="tel:${escapeHtml(c.alt_phone)}">☎ ${escapeHtml(c.alt_phone)}</a>` : ""}
                </div>
            </div>
            <div class="detail-section">${applyBlock}</div>`;
    }

    // Wire up the apply form inside the job modal
    function bindApply(container, job, onApplied) {
        const form = container.querySelector("#apply-form");
        if (!form) return;
        form.addEventListener("submit", async event => {
            event.preventDefault();
            await withButton(form.querySelector("button[type=submit]"), "Sending…", async () => {
                try {
                    const result = await api(`/api/jobs/${job.id}/apply`, { method: "POST", data: new FormData(form) });
                    toast(result.message);
                    job.applied = true;
                    if (onApplied) onApplied(job);
                } catch (error) {
                    if (error.status === 401) {
                        toast("Please log in as a Job Seeker to apply.", "error");
                        setTimeout(() => { window.location.href = "/job-seeker/login"; }, 1200);
                        return;
                    }
                    toast(error.message, "error");
                }
            });
        });
    }

    function fillJobTypes(select, types) {
        if (select.options.length > 1) return;
        select.insertAdjacentHTML("beforeend", types.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join(""));
    }

    function jobsQuery(search, type, location) {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (type) params.set("job_type", type);
        if (location) params.set("location", location);
        return `/api/jobs?${params.toString()}`;
    }

    return { jobCard, jobDetail, bindApply, matchingSkills, fillJobTypes, jobsQuery };
})();
