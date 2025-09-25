const API = (() => {
  const CSRF = () => document.cookie.split("; ").find(r => r.startsWith("mina_csrf="))?.split("=")[1];

  async function j(method, url, body) {
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": CSRF() || ""
      },
      credentials: "include",
      body: body ? JSON.stringify(body) : undefined
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || `${res.status}`);
    return data;
  }

  // Auth
  const auth = {
    me: () => j("GET", "/api/auth/me"),
    login: (email, password) => j("POST", "/api/auth/login", { email, password }),
    register: (email, password, name) => j("POST", "/api/auth/register", { email, password, name }),
    logout: () => j("POST", "/api/auth/logout"),
    refresh: () => j("POST", "/api/auth/refresh"),
    changePassword: (old_password, new_password) => j("POST", "/api/auth/change-password", { old_password, new_password }),
    requestReset: (email) => j("POST", "/api/auth/request-password-reset", { email }),
    resetPassword: (token, new_password) => j("POST", "/api/auth/reset-password", { token, new_password }),
    verifyEmail: (token) => j("POST", "/api/auth/verify-email", { token }),
  };

  // Conversations
  const conv = {
    create: (title) => j("POST", "/api/conversations", { title }),
    list: (q="", limit=20) => j("GET", `/api/conversations?q=${encodeURIComponent(q)}&limit=${limit}`),
    get: (id) => j("GET", `/api/conversations/${id}`),
    addSegment: (id, seg) => j("POST", `/api/conversations/${id}/segments`, seg),
    finalize: (id) => j("POST", `/api/conversations/${id}/finalize`),
    addHighlight: (id, h) => j("POST", `/api/conversations/${id}/highlights`, h),
    listHighlights: (id) => j("GET", `/api/conversations/${id}/highlights`),
    clearHighlights: (id) => j("DELETE", `/api/conversations/${id}/highlights`),
    addTask: (id, t) => j("POST", `/api/conversations/${id}/tasks`, t),
    listTasks: (id) => j("GET", `/api/conversations/${id}/tasks`),
    patchTask: (id, t) => j("PATCH", `/api/conversations/${id}/tasks`, t),
    share: (id) => j("POST", `/api/conversations/${id}/share`),
  };

  // Shares
  const shares = {
    get: (token) => j("GET", `/api/shares/${token}`)
  };

  // Uploads
  async function uploadFile(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/uploads", {
      method: "POST",
      credentials: "include",
      body: fd
    });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.message || `${res.status}`);
    return data;
  }

  return { auth, conv, shares, uploadFile };
})();
API.auth = {
  me: () => fetch('/auth/me').then(r=>r.json()),
  register: (payload) => fetch('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()),
  login: (payload) => fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()),
  logout: () => fetch('/auth/logout',{method:'POST'}).then(r=>r.json()),
};

API.uploads = {
  uploadFile: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return fetch('/api/uploads',{method:'POST',body:fd}).then(r=>r.json());
  }
};
