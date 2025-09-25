/**
 * Real-time Socket.IO bridge for Mina.
 * Listens to your existing WS events and persists segments to the DB in real time.
 * If the server uses different event names, edit EVENT_INTERIM / EVENT_FINAL below.
 */

window.MinaSocket = (function(){
  const EVENT_INTERIM = "transcription:interim";
  const EVENT_FINAL   = "transcription:final";
  const EVENT_ERROR   = "transcription:error";
  const EVENT_HELLO   = "server_hello";

  let socket, convId, idx = 0, onInterimCB, onFinalCB, onErrorCB;

  function connect(options) {
    const { baseUrl = undefined } = options || {};
    socket = baseUrl ? io(baseUrl, { transports: ["websocket", "polling"] }) : io({ transports: ["websocket", "polling"] });

    socket.on("connect", () => console.log("[mina] socket connected", socket.id));
    socket.on("disconnect", (r) => console.log("[mina] socket disconnected", r));
    socket.on(EVENT_HELLO, (msg) => console.log("[mina] server_hello", msg));

    socket.on(EVENT_INTERIM, async (payload) => {
      if (!convId) return;
      const { text="", start_ms=0, end_ms=0 } = payload || {};
      try {
        await API.conv.addSegment(convId, { idx: idx++, start_ms, end_ms, text, is_final: false });
        if (onInterimCB) onInterimCB(payload);
      } catch (e) {
        console.error("[mina] persist interim failed", e);
      }
    });

    socket.on(EVENT_FINAL, async (payload) => {
      if (!convId) return;
      const { text="", start_ms=0, end_ms=0 } = payload || {};
      try {
        await API.conv.addSegment(convId, { idx: idx++, start_ms, end_ms, text, is_final: true });
        if (onFinalCB) onFinalCB(payload);
      } catch (e) {
        console.error("[mina] persist final failed", e);
      }
    });

    socket.on(EVENT_ERROR, (err) => {
      console.error("[mina] transcription error", err);
      if (onErrorCB) onErrorCB(err);
    });
  }

  async function startSession(title="Untitled Conversation") {
    const r = await API.conv.create(title);
    convId = r.id; idx = 0;
    return convId;
  }

  async function stopSession() {
    if (!convId) return;
    await API.conv.finalize(convId);
    const done = convId; convId = null; idx = 0;
    return done;
  }

  return {
    connect,
    startSession,
    stopSession,
    onInterim(cb){ onInterimCB = cb; },
    onFinal(cb){ onFinalCB = cb; },
    onError(cb){ onErrorCB = cb; }
  };
})();