async function post(url, body){
  const r = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify(body)});
  const j = await r.json().catch(()=>({}));
  if(!r.ok || j.ok===false) throw new Error(j.error||("HTTP_"+r.status));
  return j;
}
async function me(){
  const r = await fetch("/auth/me",{credentials:"include"});
  try{ const j = await r.json(); return j.user||null; }catch(e){ return null; }
}
(async function init(){
  const user = await me();
  if(user){ location.href="/app"; return; }
  const $ = (id)=>document.getElementById(id);
  const msg = $("msg");
  $("btn-login").onclick = async ()=>{
    msg.textContent=""; try{
      await post("/auth/login",{email:$("email").value,password:$("password").value});
      location.href="/app";
    }catch(e){ msg.textContent = "Login failed: "+e.message; }
  };
  $("btn-register").onclick = async ()=>{
    msg.textContent=""; try{
      await post("/auth/register",{name:$("name").value,email:$("email").value,password:$("password").value});
      location.href="/app";
    }catch(e){ msg.textContent = "Sign up failed: "+e.message; }
  };
})();
