/**
 * Authentication Helper for K6 Load Tests
 * 
 * Handles authentication for protected endpoints.
 * Supports session-based and token-based auth.
 */

import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL } from './config.js';

/**
 * Create a test user session (for write operations)
 * NOTE: This requires test user credentials to be available
 */
export function createTestSession() {
  // For now, we'll use a mock approach that tests can call
  // In production, this would authenticate with real test credentials
  
  const loginPayload = {
    username: `loadtest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    email: `loadtest_${Date.now()}@test.mina.app`,
    password: 'LoadTest123!',
  };
  
  return {
    username: loginPayload.username,
    email: loginPayload.email,
    authenticated: false,
    cookies: {},
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  };
}

/**
 * Attempt to authenticate (returns mock session for now)
 * 
 * To enable real authentication in tests:
 * 1. Create test user in database
 * 2. Update this function to perform real login
 * 3. Extract and return session cookies/tokens
 */
export function authenticate(session) {
  // For load testing without authentication
  // In production, uncomment this code:
  
  /*
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: session.username,
    password: session.password,
  }), {
    headers: session.headers,
  });
  
  if (loginRes.status === 200) {
    // Extract session cookies
    const cookies = loginRes.cookies;
    session.cookies = cookies;
    session.authenticated = true;
    
    // Or extract JWT token if using token auth
    const responseBody = JSON.parse(loginRes.body);
    if (responseBody.token) {
      session.headers['Authorization'] = `Bearer ${responseBody.token}`;
    }
  }
  
  return session;
  */
  
  // Mock authentication for testing
  session.authenticated = true;
  return session;
}

/**
 * Get request params with authentication
 */
export function getAuthParams(session) {
  return {
    headers: session.headers,
    cookies: session.cookies || {},
    tags: { authenticated: session.authenticated },
  };
}

/**
 * Check if endpoint requires authentication
 * Returns true if 401/403, false if 200/302
 */
export function requiresAuth(endpoint) {
  const res = http.get(`${BASE_URL}${endpoint}`);
  return res.status === 401 || res.status === 403;
}

export default {
  createTestSession,
  authenticate,
  getAuthParams,
  requiresAuth,
};
