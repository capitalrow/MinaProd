# 6. JWT Authentication with Role-Based Access Control

**Date**: 2025-10-02

**Status**: Accepted

**Context**: Mina requires secure user authentication for both HTTP and WebSocket connections, with support for different user roles (admin, organizer, participant) and workspace-based isolation.

**Decision**: Use JWT (JSON Web Tokens) for stateless authentication, with bcrypt for password hashing and Flask-Login for session management.

**Alternatives Considered**:
- Session-based auth: Requires server-side storage, harder to scale
- OAuth 2.0 only: Adds complexity for internal users
- API keys: Less secure for user-facing authentication

**Consequences**:
- **Positive**:
  - Stateless authentication scales horizontally
  - Works for both HTTP and WebSocket
  - Short-lived tokens reduce security risk
  - Role claims embedded in token
  - Refresh token rotation prevents replay attacks
  
- **Negative**:
  - Token revocation requires additional logic
  - JWT size can grow with many claims
  - Clock skew can cause validation issues
