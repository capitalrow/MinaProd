window.API = {
  conv: {
    async create(title){ const r = await fetch("/api/conversations",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({title})}); return r.json(); },
    async list(){ const r = await fetch("/api/conversations",{credentials:"include"}); return r.json(); },
    async addSegment(id, seg){ const r = await fetch(`/api/conversations/${id}/segments`,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify(seg)}); return r.json(); },
    async get(id){ const r = await fetch(`/api/conversations/${id}`,{credentials:"include"}); return r.json(); },
    async finalize(id){ const r = await fetch(`/api/conversations/${id}/finalize`,{method:"POST",credentials:"include"}); return r.json(); },
  }
};
