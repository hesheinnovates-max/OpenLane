// =========================================================
// Public job listings page (/jobs). Anyone can browse,
// a job seeker account is needed to apply inside OpenLane.
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    const { api, escapeHtml, openModal } = OpenLane;
    const $ = id => document.getElementById(id);
    const state = { me: null, jobs: [], skills: [] };

    async function loadMe() {
        try {
            state.me = await api("/api/me");
        } catch (error) {
            state.me = null;
        }
        const actions = $("top-actions");
        if (state.me && state.me.role === "job_seeker") {
            actions.innerHTML = `<span class="top-user">${escapeHtml(state.me.name)}</span><a class="top-link" href="/job-seeker/dashboard">My dashboard</a>`;
            try {
                state.skills = (await api("/api/job-seeker/skills")).skills;
            } catch (error) {
                state.skills = [];
            }
        } else if (state.me && state.me.role === "company") {
            actions.innerHTML = `<span class="top-user">${escapeHtml(state.me.name)}</span><a class="top-link" href="/company/dashboard">Company dashboard</a>`;
        } else {
            actions.innerHTML = `<a class="top-link" href="/job-seeker/login">Log in</a><a class="top-link" href="/job-seeker/register">Sign up</a>`;
        }
    }

    async function loadJobs() {
        try {
            const result = await api(OpenLaneJobs.jobsQuery(
                $("job-search").value.trim(),
                $("job-type-filter").value,
                $("job-location-filter").value.trim()
            ));
            state.jobs = result.jobs;
            OpenLaneJobs.fillJobTypes($("job-type-filter"), result.job_types);
            render();
            openFromHash();
        } catch (error) {
            $("jobs-list").innerHTML = `<div class="empty"><strong>Could not load jobs</strong>${escapeHtml(error.message)}</div>`;
        }
    }

    function render() {
        $("job-count").textContent = `${state.jobs.length} open job${state.jobs.length === 1 ? "" : "s"}`;
        if (!state.jobs.length) {
            $("jobs-list").innerHTML = `<div class="empty"><strong>No jobs found</strong>Try different words, or check back soon.</div>`;
            return;
        }
        $("jobs-list").innerHTML = state.jobs.map(job => OpenLaneJobs.jobCard(job, state.skills)).join("");
    }

    function showJob(job) {
        const body = $("job-modal-body");
        body.innerHTML = OpenLaneJobs.jobDetail(job, { skills: state.skills, isJobSeeker: state.me && state.me.role === "job_seeker" });
        OpenLaneJobs.bindApply(body, job, applied => {
            showJob(applied);
            render();
        });
        history.replaceState(null, "", `#job-${job.id}`);
        openModal("job-modal");
    }

    // Allow sharing a link straight to one job: /jobs#job-12
    function openFromHash() {
        const match = location.hash.match(/^#job-(\d+)$/);
        if (!match) return;
        const job = state.jobs.find(j => String(j.id) === match[1]);
        if (job) showJob(job);
    }

    $("jobs-list").addEventListener("click", event => {
        const card = event.target.closest("[data-job-id]");
        if (!card) return;
        const job = state.jobs.find(j => String(j.id) === card.dataset.jobId);
        if (job) showJob(job);
    });

    let timer;
    ["job-search", "job-type-filter", "job-location-filter"].forEach(id => {
        $(id).addEventListener("input", () => {
            clearTimeout(timer);
            timer = setTimeout(loadJobs, 300);
        });
    });

    loadMe().then(loadJobs);
});
