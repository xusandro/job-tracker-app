import { useEffect, useState } from "react";

const emptyForm = {
  company: "",
  title: "",
  website: "",
  job_link: "",
  description: "",
  status: "in_progress",
};

const statusOptions = [
  { value: "in_progress", label: "In Progress" },
  { value: "interview", label: "Interview" },
  { value: "offer", label: "Offer" },
  { value: "rejected", label: "Rejected" },
];

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    credentials: "include",
    ...options,
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new Error(payload?.error || "Request failed.");
  }

  return payload;
}

function AuthForm({ mode, onSubmit, loading }) {
  const [form, setForm] = useState({
    username: "",
    password: "",
    birth_date: "",
    new_password: "",
  });

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <p className="eyebrow">Job Tracker</p>
        <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
        <p className="muted">
          {mode === "login"
            ? "Log in to manage your applications."
            : mode === "register"
              ? "Create a new account to save your applications."
              : "Reset your password with the recovery details saved at sign-up."}
        </p>

        <form onSubmit={handleSubmit} className="stack">
          <label>
            <span>Username</span>
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Username"
              required
            />
          </label>

          {mode !== "reset" ? (
            <label>
              <span>Password</span>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                placeholder={mode === "login" ? "Password" : "At least 6 characters"}
                required
              />
            </label>
          ) : null}

          {mode !== "login" ? (
            <label>
              <span>Birth Date</span>
              <input
                name="birth_date"
                type="date"
                value={form.birth_date}
                onChange={handleChange}
                required
              />
            </label>
          ) : null}

          {mode === "reset" ? (
            <label>
              <span>New Password</span>
              <input
                name="new_password"
                type="password"
                value={form.new_password}
                onChange={handleChange}
                placeholder="At least 6 characters"
                required
              />
            </label>
          ) : null}

          <button type="submit" disabled={loading}>
            {loading
              ? "Working..."
              : mode === "login"
                ? "Log In"
                : mode === "register"
                  ? "Register"
                  : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}

function JobForm({ initialValues, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(initialValues);

  useEffect(() => {
    setForm(initialValues);
  }, [initialValues]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <label>
        <span>Company</span>
        <input name="company" value={form.company} onChange={handleChange} required />
      </label>

      <label>
        <span>Title</span>
        <input name="title" value={form.title} onChange={handleChange} required />
      </label>

      <label>
        <span>Company Website</span>
        <input name="website" value={form.website} onChange={handleChange} />
      </label>

      <label>
        <span>Job Link</span>
        <input name="job_link" value={form.job_link} onChange={handleChange} />
      </label>

      <label>
        <span>Description / Notes</span>
        <textarea
          name="description"
          value={form.description}
          onChange={handleChange}
          rows="8"
        />
      </label>

      <label>
        <span>Status</span>
        <select name="status" value={form.status} onChange={handleChange}>
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <div className="actions">
        <button type="submit" disabled={loading}>
          {loading ? "Saving..." : "Save Job"}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function Dashboard({
  user,
  jobs,
  selectedJob,
  search,
  setSearch,
  onRefresh,
  onSelect,
  onCreate,
  onUpdate,
  onDelete,
  onStartCreate,
  onStartEdit,
  onQuickStatusChange,
  formMode,
  setFormMode,
  formLoading,
  onLogout,
}) {
  const isCreating = formMode === "create";
  const isEditing = formMode === "edit";

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Job Tracker</p>
          <h1>{user.username}'s dashboard</h1>
        </div>

        <div className="topbar-actions">
          <button onClick={onStartCreate}>Add job</button>
          <button className="secondary" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <section className="hero">
        <div>
          <h2>Keep every application in one place</h2>
          <p>
            Search your job pipeline, update details, and keep interview notes tied to
            each application.
          </p>
        </div>

        <form
          className="search-bar"
          onSubmit={(event) => {
            event.preventDefault();
            onRefresh(search);
          }}
        >
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by company, title, website, link, or notes"
          />
          <button type="submit">Search</button>
        </form>
      </section>

      <div className="content-grid">
        <section className="panel">
          <div className="panel-header">
            <h3>Applications</h3>
            <span className="pill">{jobs.length}</span>
          </div>

          {jobs.length === 0 ? (
            <p className="empty-state">No jobs yet. Add your first application.</p>
          ) : (
            <div className="job-list">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className={`job-card ${selectedJob?.id === job.id ? "active" : ""}`}
                >
                  <button className="job-card-main" onClick={() => onSelect(job.id)}>
                    <strong>{job.title}</strong>
                    <span>{job.company}</span>
                  </button>
                  <div className={`status-chip ${job.status}`}>{job.status.replace("_", " ")}</div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          {isCreating || isEditing ? (
            <>
              <div className="panel-header">
                <h3>{isCreating ? "Add a new job" : "Edit job"}</h3>
              </div>
              <JobForm
                initialValues={
                  isEditing && selectedJob
                    ? {
                        company: selectedJob.company || "",
                        title: selectedJob.title || "",
                        website: selectedJob.website || "",
                        job_link: selectedJob.job_link || "",
                        description: selectedJob.description || "",
                      }
                    : emptyForm
                }
                onSubmit={isCreating ? onCreate : onUpdate}
                onCancel={() => setFormMode("view")}
                loading={formLoading}
              />
            </>
          ) : selectedJob ? (
            <>
              <div className="panel-header">
                <h3>{selectedJob.title}</h3>
                <div className="actions">
                  <button className="secondary" onClick={onStartEdit}>
                    Edit
                  </button>
                  <button className="danger" onClick={() => onDelete(selectedJob.id)}>
                    Delete
                  </button>
                </div>
              </div>

              <div className="detail-grid">
                <div>
                  <span className="label">Company</span>
                  <p>{selectedJob.company}</p>
                </div>
                <div>
                  <span className="label">Website</span>
                  <p>{selectedJob.website || "Not provided"}</p>
                </div>
                <div>
                  <span className="label">Job Link</span>
                  <p>{selectedJob.job_link || "Not provided"}</p>
                </div>
                <div>
                  <span className="label">Status</span>
                  <div className="status-actions">
                    {statusOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={
                          selectedJob.status === option.value ? "status-button active" : "status-button"
                        }
                        onClick={() => onQuickStatusChange(option.value)}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="label">Created</span>
                  <p>{new Date(selectedJob.created_at).toLocaleString()}</p>
                </div>
              </div>

              <div>
                <span className="label">Notes</span>
                <div className="notes-box">
                  {selectedJob.description || "No notes yet."}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-detail">
              <h3>Select a job</h3>
              <p>Choose an application from the list to view or edit its details.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default function App() {
  const [authMode, setAuthMode] = useState("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [user, setUser] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [formMode, setFormMode] = useState("view");
  const [search, setSearch] = useState("");

  async function loadSession() {
    const payload = await apiRequest("/api/session");
    if (payload.authenticated) {
      setUser(payload.user);
      await refreshJobs(search);
    }
  }

  async function refreshJobs(query = "") {
    const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
    const payload = await apiRequest(`/api/jobs${suffix}`);
    setJobs(payload.jobs);
    setSelectedJob((current) => {
      if (!payload.jobs.length) {
        return null;
      }

      if (current) {
        return payload.jobs.find((job) => job.id === current.id) || payload.jobs[0];
      }

      return payload.jobs[0];
    });
  }

  useEffect(() => {
    loadSession().catch(() => {
      setUser(null);
    });
  }, []);

  async function handleRegister(form) {
    setAuthLoading(true);
    try {
      await apiRequest("/api/register", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setMessage("Registration successful. Please log in.");
      setAuthMode("login");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleResetPassword(form) {
    setAuthLoading(true);
    try {
      const payload = await apiRequest("/api/reset-password", {
        method: "POST",
        body: JSON.stringify({
          username: form.username,
          birth_date: form.birth_date,
          new_password: form.new_password,
        }),
      });
      setMessage(payload.message);
      setAuthMode("login");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogin(form) {
    setAuthLoading(true);
    try {
      const payload = await apiRequest("/api/login", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setUser(payload.user);
      setMessage("Logged in successfully.");
      setSearch("");
      setFormMode("view");
      await refreshJobs();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    await apiRequest("/api/logout", { method: "POST" });
    setUser(null);
    setJobs([]);
    setSelectedJob(null);
    setMessage("Logged out successfully.");
    setAuthMode("login");
  }

  async function handleSelectJob(jobId) {
    try {
      const payload = await apiRequest(`/api/jobs/${jobId}`);
      setSelectedJob(payload.job);
      setFormMode("view");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleCreateJob(form) {
    setFormLoading(true);
    try {
      const payload = await apiRequest("/api/jobs", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setMessage(payload.message);
      setFormMode("view");
      await refreshJobs(search);
      setSelectedJob(payload.job);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setFormLoading(false);
    }
  }

  async function handleUpdateJob(form) {
    if (!selectedJob) {
      return;
    }

    setFormLoading(true);
    try {
      const payload = await apiRequest(`/api/jobs/${selectedJob.id}`, {
        method: "PUT",
        body: JSON.stringify(form),
      });
      setMessage(payload.message);
      setSelectedJob(payload.job);
      setFormMode("view");
      await refreshJobs(search);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDeleteJob(jobId) {
    const confirmed = window.confirm("Delete this job application?");
    if (!confirmed) {
      return;
    }

    try {
      const payload = await apiRequest(`/api/jobs/${jobId}`, { method: "DELETE" });
      setMessage(payload.message);
      setFormMode("view");
      await refreshJobs(search);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleQuickStatusChange(status) {
    if (!selectedJob) {
      return;
    }

    setFormLoading(true);
    try {
      const payload = await apiRequest(`/api/jobs/${selectedJob.id}`, {
        method: "PUT",
        body: JSON.stringify({
          company: selectedJob.company,
          title: selectedJob.title,
          website: selectedJob.website || "",
          job_link: selectedJob.job_link || "",
          description: selectedJob.description || "",
          status,
        }),
      });
      setSelectedJob(payload.job);
      setMessage(`Status updated to ${status.replace("_", " ")}.`);
      await refreshJobs(search);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setFormLoading(false);
    }
  }

  return (
    <>
      {message ? <div className="toast">{message}</div> : null}
      {user ? (
        <Dashboard
          user={user}
          jobs={jobs}
          selectedJob={selectedJob}
          search={search}
          setSearch={setSearch}
          onRefresh={refreshJobs}
          onSelect={handleSelectJob}
          onCreate={handleCreateJob}
          onUpdate={handleUpdateJob}
          onDelete={handleDeleteJob}
          onStartCreate={() => setFormMode("create")}
          onStartEdit={() => setFormMode("edit")}
          onQuickStatusChange={handleQuickStatusChange}
          formMode={formMode}
          setFormMode={setFormMode}
          formLoading={formLoading}
          onLogout={handleLogout}
        />
      ) : (
        <div>
          <AuthForm
            mode={authMode}
            onSubmit={
              authMode === "login"
                ? handleLogin
                : authMode === "register"
                  ? handleRegister
                  : handleResetPassword
            }
            loading={authLoading}
          />
          <p className="auth-toggle">
            {authMode === "login" ? "Need an account?" : "Want to go back?"}{" "}
            <button className="link-button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
              {authMode === "login" ? "Register" : "Log in"}
            </button>
            {authMode === "login" ? (
              <>
                {" "}
                |{" "}
                <button className="link-button" onClick={() => setAuthMode("reset")}>
                  Forgot password?
                </button>
              </>
            ) : null}
          </p>
        </div>
      )}
    </>
  );
}
