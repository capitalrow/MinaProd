import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Trend, Counter } from 'k6/metrics';

let latency = new Trend('latency');
let errors = new Counter('errors');

export let options = {
  vus: 50,               // virtual users
  duration: '1m',
  thresholds: {
    'errors': ['count<5'],
    'latency{type:send}': ['avg<300'],
  },
};

export default function () {
  const url = __ENV.SOCKET_URL || 'ws://localhost:5000/socket.io/?EIO=4&transport=websocket';
  const res = ws.connect(url, {}, function (socket) {
    socket.on('open', () => {
      for (let i = 0; i < 10; i++) {
        const t0 = Date.now();
        socket.send(JSON.stringify({ event: 'transcribe_chunk', data: { text: 'loadtest message' } }));
        latency.add(Date.now() - t0, { type: 'send' });
        sleep(0.1);
      }
      socket.close();
    });

    socket.on('error', (e) => {
      errors.add(1);
      console.error('Socket error:', e);
    });
  });

  check(res, { 'status is 101': (r) => r && r.status === 101 });
  sleep(1);
}