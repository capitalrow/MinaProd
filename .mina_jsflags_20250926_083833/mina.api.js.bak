window.API = {
  auth: {
    async register(email, password, name){ 
      const r = await fetch("/auth/register",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({email, password, name})
      }); 
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.error || 'Registration failed');
      }
      return r.json(); 
    },
    async login(email, password){ 
      const r = await fetch("/auth/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({email, password})
      }); 
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.error || 'Login failed');
      }
      return r.json(); 
    },
    async logout(){ 
      const r = await fetch("/auth/logout",{
        method:"POST",
        credentials:"include"
      }); 
      return r.json(); 
    },
    async me(){ 
      const r = await fetch("/auth/me",{
        credentials:"include"
      }); 
      if (!r.ok) throw new Error('Not authenticated');
      return r.json(); 
    },
    async requestReset(email){ 
      const r = await fetch("/auth/request-reset",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({email})
      }); 
      return r.json(); 
    },
    async resetPassword(token, password){ 
      const r = await fetch("/auth/reset-password",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({token, password})
      }); 
      return r.json(); 
    },
    async changePassword(currentPassword, newPassword){ 
      const r = await fetch("/auth/change-password",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({current_password: currentPassword, new_password: newPassword})
      }); 
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.error || 'Password change failed');
      }
      return r.json(); 
    },
    async verifyEmail(token){ 
      const r = await fetch("/auth/verify-email",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        credentials:"include",
        body:JSON.stringify({token})
      }); 
      return r.json(); 
    }
  },
  conv: {
    async create(title){ const r = await fetch("/api/conversations",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({title})}); return r.json(); },
    async list(){ const r = await fetch("/api/conversations",{credentials:"include"}); return r.json(); },
    async addSegment(id, seg){ const r = await fetch(`/api/conversations/${id}/segments`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify(seg)}); return r.json(); },
    async get(id){ const r = await fetch(`/api/conversations/${id}`,{credentials:"include"}); return r.json(); },
    async finalize(id){ const r = await fetch(`/api/conversations/${id}/finalize`,{method:"POST",credentials:"include"}); return r.json(); },
    async addHighlight(id, highlight){ const r = await fetch(`/api/conversations/${id}/highlights`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify(highlight)}); return r.json(); },
    async listHighlights(id){ const r = await fetch(`/api/conversations/${id}/highlights`,{credentials:"include"}); return r.json(); },
    async addTask(id, task){ const r = await fetch(`/api/conversations/${id}/tasks`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify(task)}); return r.json(); },
    async listTasks(id){ const r = await fetch(`/api/conversations/${id}/tasks`,{credentials:"include"}); return r.json(); },
    async share(id){ const r = await fetch(`/api/conversations/${id}/share`,{method:"POST",credentials:"include"}); return r.json(); }
  },
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const r = await fetch('/api/upload', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    if (!r.ok) {
      const err = await r.json();
      throw new Error(err.error || 'Upload failed');
    }
    return r.json();
  }
};
