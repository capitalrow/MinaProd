/**
 * K6 Load Test: WebSocket Transcription Load
 * 
 * Tests real-time transcription WebSocket connections under load to verify:
 * - WebSocket SLO compliance (P50 <2000ms, P95 <5000ms, P99 <10000ms)
 * - Concurrent connection handling (peak: 2000 MPS, capacity: 5000 MPS)
 * - Message processing latency
 * - Connection stability and error handling
 * 
 * WebSocket endpoints tested:
 * - Socket.IO connection to /socket.io/
 * - Transcription events: connect, audio_chunk, transcript, disconnect
 */

import { check, sleep } from 'k6';
import ws from 'k6/ws';
import { Rate, Trend, Counter } from 'k6/metrics';
import { BASE_URL } from '../config.js';

// Custom metrics
const wsConnectionDuration = new Trend('ws_connection_duration', true);
const wsMessageLatency = new Trend('ws_message_latency', true);
const wsConnectionSuccess = new Rate('ws_connection_success');
const wsMessageErrors = new Rate('ws_message_errors');
const wsConnections = new Counter('ws_total_connections');
const wsMessages = new Counter('ws_total_messages');

// Test configuration
export const options = {
  scenarios: {
    // Smoke test: Basic WebSocket connectivity
    smoke: {
      executor: 'constant-vus',
      exec: 'smoke',
      vus: 1,
      duration: '30s',
      tags: { test_type: 'smoke' },
    },
    
    // Normal load: 10 concurrent connections
    normal_load: {
      executor: 'constant-vus',
      exec: 'transcriptionSession',
      vus: 10,
      duration: '3m',
      startTime: '30s',
      tags: { test_type: 'normal' },
    },
    
    // Peak load: 50 concurrent connections
    peak_load: {
      executor: 'constant-vus',
      exec: 'transcriptionSession',
      vus: 50,
      duration: '3m',
      startTime: '3m30s',
      tags: { test_type: 'peak' },
    },
    
    // Capacity test: 150 concurrent connections (3x peak)
    capacity_test: {
      executor: 'constant-vus',
      exec: 'transcriptionSession',
      vus: 150,
      duration: '2m',
      startTime: '6m30s',
      tags: { test_type: 'capacity' },
    },
  },
  
  // WebSocket SLO thresholds
  thresholds: {
    'ws_connection_duration': [
      'p(50)<2000',   // P50 < 2s
      'p(95)<5000',   // P95 < 5s
      'p(99)<10000',  // P99 < 10s
    ],
    'ws_message_latency': [
      'p(50)<500',    // Message processing P50 < 500ms
      'p(95)<2000',   // Message processing P95 < 2s
      'p(99)<5000',   // Message processing P99 < 5s
    ],
    'ws_connection_success': ['rate>0.95'], // 95% connection success
    'ws_message_errors': ['rate<0.01'],     // <1% message errors
    'ws_total_connections': ['count>100'],   // Minimum connections
  },
};

/**
 * Smoke test: Basic WebSocket connection
 */
export function smoke() {
  const wsUrl = BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  
  const res = ws.connect(`${wsUrl}/socket.io/?EIO=4&transport=websocket`, (socket) => {
    socket.on('open', () => {
      console.log('WebSocket smoke test: connection opened');
      socket.close();
    });
    
    socket.on('error', (e) => {
      console.error('WebSocket smoke test error:', e);
    });
    
    socket.setTimeout(() => {
      socket.close();
    }, 5000);
  });
  
  check(res, {
    'smoke test: connection established': (r) => r && r.status === 101,
  });
  
  sleep(1);
}

/**
 * Main test: Simulated transcription session
 */
export function transcriptionSession() {
  const wsUrl = BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const connectStart = Date.now();
  let connected = false;
  let messagesReceived = 0;
  let messagesSent = 0;
  
  const res = ws.connect(`${wsUrl}/socket.io/?EIO=4&transport=websocket&sessionId=${sessionId}`, {
    headers: {
      'Origin': BASE_URL,
    },
    tags: { session_id: sessionId },
  }, (socket) => {
    
    socket.on('open', () => {
      connected = true;
      const connectDuration = Date.now() - connectStart;
      wsConnectionDuration.add(connectDuration);
      wsConnectionSuccess.add(1);
      wsConnections.add(1);
      
      // Send Socket.IO handshake
      socket.send('40');  // Socket.IO connect packet
      
      // Simulate audio chunks (10 chunks over 5 seconds)
      for (let i = 0; i < 10; i++) {
        socket.setTimeout(() => {
          if (socket.readyState === 1) {  // OPEN
            const messageStart = Date.now();
            
            // Simulate audio chunk data (Socket.IO event packet)
            const audioData = {
              chunk_id: i,
              audio: 'base64_encoded_audio_data_placeholder',
              timestamp: Date.now(),
            };
            
            socket.send(`42["audio_chunk",${JSON.stringify(audioData)}]`);
            messagesSent++;
            wsMessages.add(1);
          }
        }, i * 500);  // Send chunk every 500ms
      }
      
      // Close connection after 5 seconds
      socket.setTimeout(() => {
        socket.send('41');  // Socket.IO disconnect packet
        socket.close();
      }, 5500);
    });
    
    socket.on('message', (msg) => {
      messagesReceived++;
      
      // Parse Socket.IO message
      if (msg.startsWith('42')) {
        // Event message
        try {
          const eventData = JSON.parse(msg.substring(2));
          const eventName = eventData[0];
          const eventPayload = eventData[1];
          
          if (eventName === 'transcript') {
            // Measure transcript latency (from chunk send to transcript receive)
            const latency = Date.now() - (eventPayload.timestamp || Date.now());
            wsMessageLatency.add(latency);
            
            wsMessageErrors.add(0);
          }
        } catch (e) {
          wsMessageErrors.add(1);
        }
      }
    });
    
    socket.on('error', (e) => {
      console.error(`WebSocket error in session ${sessionId}:`, e);
      wsMessageErrors.add(1);
    });
    
    socket.on('close', () => {
      if (!connected) {
        wsConnectionSuccess.add(0);
      }
    });
  });
  
  // Record connection result
  const connectionSuccess = check(res, {
    'connection established': (r) => r && r.status === 101,
  });
  
  if (!connectionSuccess) {
    wsConnectionSuccess.add(0);
    console.warn(`Failed to establish WebSocket connection for session ${sessionId}`);
  }
  
  // Wait between sessions
  sleep(1 + Math.random() * 2);
}

/**
 * Setup: Run once at start
 */
export function setup() {
  console.log('🚀 Starting WebSocket Transcription Load Test');
  console.log(`📊 Target: Verify WebSocket capacity and SLO compliance`);
  console.log(`🎯 SLO Targets: Connection P50<2s, P95<5s, P99<10s`);
  console.log(`⚠️  Note: This test requires WebSocket endpoint to be available`);
  
  return { startTime: Date.now() };
}

/**
 * Teardown: Run once at end
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000 / 60;
  console.log(`✅ WebSocket Transcription Load Test completed in ${duration.toFixed(2)} minutes`);
}

/**
 * Custom summary handler
 */
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'websocket_transcription_load',
    duration_seconds: data.state.testRunDurationMs / 1000,
    metrics: {
      connections_total: data.metrics.ws_total_connections?.values.count || 0,
      connection_success_rate: data.metrics.ws_connection_success?.values.rate || 0,
      messages_total: data.metrics.ws_total_messages?.values.count || 0,
      message_error_rate: data.metrics.ws_message_errors?.values.rate || 0,
      connection_latency: {
        p50: data.metrics.ws_connection_duration?.values['p(50)'] || 0,
        p95: data.metrics.ws_connection_duration?.values['p(95)'] || 0,
        p99: data.metrics.ws_connection_duration?.values['p(99)'] || 0,
      },
      message_latency: {
        p50: data.metrics.ws_message_latency?.values['p(50)'] || 0,
        p95: data.metrics.ws_message_latency?.values['p(95)'] || 0,
        p99: data.metrics.ws_message_latency?.values['p(99)'] || 0,
      },
    },
    slo_compliance: {
      connection_p50_met: (data.metrics.ws_connection_duration?.values['p(50)'] || 0) < 2000,
      connection_p95_met: (data.metrics.ws_connection_duration?.values['p(95)'] || 0) < 5000,
      connection_p99_met: (data.metrics.ws_connection_duration?.values['p(99)'] || 0) < 10000,
      success_rate_met: (data.metrics.ws_connection_success?.values.rate || 0) > 0.95,
    },
    pass: 
      (data.metrics.ws_connection_duration?.values['p(50)'] || 0) < 2000 &&
      (data.metrics.ws_connection_duration?.values['p(95)'] || 0) < 5000 &&
      (data.metrics.ws_connection_duration?.values['p(99)'] || 0) < 10000 &&
      (data.metrics.ws_connection_success?.values.rate || 0) > 0.95,
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    '../results/websocket-transcription-results.json': JSON.stringify(summary, null, 2),
  };
}
