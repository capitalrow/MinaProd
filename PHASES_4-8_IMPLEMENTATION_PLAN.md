# Phases 4-8 Implementation Plan
**Remaining Tasks: 105/268 (39%)**  
**Target: Production-Ready Launch**

---

## 🎯 OVERVIEW

This document provides a detailed, actionable plan to complete Phases 4-8 of the Mina roadmap. These phases transform Mina from a working prototype into a production-ready SaaS platform.

**Current State:** Core platform works (transcription, AI, collaboration)  
**Missing:** Business operations (billing, admin), legal compliance, team features, advanced tooling

---

## 📋 PHASE 4: ADMIN CORE (32 remaining tasks)

**Goal:** Build admin dashboard and billing infrastructure for business operations  
**Priority:** 🔴 CRITICAL - Required for public launch

### **4.1 Billing System (10 tasks)**

**Status:** Models + Stripe service exist, need UI integration

**Tasks:**
1. ✅ **Stripe Integration Service** (DONE - `services/stripe_service.py`)
2. ✅ **Billing Models** (DONE - Customer, Subscription in `models/core_models.py`)
3. ❌ **Billing Dashboard UI**
   - Create `/billing` route with pricing plans
   - Display current subscription status
   - Show usage metrics and limits
   - Design: Crown+ glassmorphism cards
4. ❌ **Stripe Checkout Flow**
   - Implement checkout session creation
   - Add success/cancel redirect pages
   - Handle 3D Secure authentication
5. ❌ **Customer Portal**
   - Link to Stripe billing portal
   - Allow subscription management
   - Support plan upgrades/downgrades
6. ❌ **Webhook Handler**
   - Verify webhook signatures
   - Handle subscription.updated events
   - Handle payment_intent.succeeded/failed
   - Update database accordingly
7. ❌ **Usage Limits Enforcement**
   - Track monthly transcription minutes
   - Block requests when limit exceeded
   - Show upgrade prompts
8. ❌ **Billing Email Templates**
   - Payment successful
   - Payment failed
   - Subscription renewed
   - Trial ending
   - Invoice receipts
9. ❌ **Plan Comparison Page**
   - Free, Pro, Team, Enterprise tiers
   - Feature comparison table
   - CTAs for each tier
10. ❌ **Billing Tests**
    - Unit tests for Stripe service
    - Integration tests for webhooks
    - E2E checkout flow test

---

### **4.2 Admin Dashboard (15 tasks)**

**Status:** No admin UI exists

**Tasks:**
1. ❌ **Admin Auth & Permissions**
   - Create is_admin flag on User model
   - Protect admin routes with decorator
   - RBAC for admin actions
2. ❌ **Admin Navigation**
   - `/admin` route
   - Sidebar with: Users, Metrics, Support, Billing, Feature Flags
3. ❌ **User Management Dashboard**
   - List all users (paginated table)
   - Search/filter by email, plan, status
   - View user details (activity, usage, sessions)
   - Actions: Suspend, Delete, Impersonate
4. ❌ **User Detail Page**
   - Profile info
   - Subscription status
   - Usage statistics (minutes, sessions, storage)
   - Activity timeline
   - Session history
5. ❌ **Metrics Dashboard**
   - Total users, active users, churn rate
   - MRR, ARR, LTV
   - Transcription minutes (total, by user, by day)
   - Chart.js visualizations
6. ❌ **Support Ticket System**
   - Ticket model (user_id, subject, description, status, priority)
   - User-facing: Submit ticket form
   - Admin-facing: Ticket queue, assignment, responses
   - Email notifications
7. ❌ **Support Dashboard**
   - Open, in-progress, closed tickets
   - Assign to admin users
   - Canned responses library
   - Priority sorting
8. ❌ **Live Chat Widget**
   - Real-time chat (Socket.IO)
   - Admin inbox for incoming chats
   - Presence indicators
   - Chat history
9. ❌ **Knowledge Base**
   - Article model (title, content, category, tags)
   - Public KB pages
   - Search functionality
   - Admin: Create/edit articles
10. ❌ **Usage Analytics**
    - Top users by transcription minutes
    - Peak usage times
    - Feature adoption metrics
    - Retention cohorts
11. ❌ **Revenue Dashboard**
    - MRR growth chart
    - Subscription breakdown by plan
    - Churn analysis
    - Stripe integration for payment data
12. ❌ **System Health Monitor**
    - Server uptime, response times
    - Error rate tracking
    - Database performance
    - WebSocket connection health
13. ❌ **Announcement System**
    - Announcement model (title, message, type, target_users)
    - Admin: Create announcements
    - User: Banner/modal for announcements
    - Dismiss functionality
14. ❌ **Audit Log**
    - Track admin actions (user edits, deletions, config changes)
    - Searchable log viewer
    - Compliance requirement
15. ❌ **Admin Tests**
    - Permission enforcement tests
    - User management E2E
    - Support ticket workflow

---

### **4.3 Limits & Quotas (7 tasks)**

**Status:** No enforcement exists

**Tasks:**
1. ❌ **Usage Tracking Service**
   - Track transcription minutes per user per month
   - Store in UsageMetrics table
   - Reset monthly counters
2. ❌ **Plan Limits Configuration**
   - Free: 60 min/month, 10 sessions
   - Pro: 600 min/month, unlimited sessions
   - Team: 2000 min/month, team features
   - Enterprise: Unlimited, custom
3. ❌ **Limit Enforcement Middleware**
   - Check limits before starting transcription
   - Return 403 with upgrade message if exceeded
4. ❌ **Usage Display**
   - Show current usage on dashboard
   - Progress bars for limits
   - Days until reset
5. ❌ **Upgrade Prompts**
   - Modal when limit approaching (80%)
   - Block with upgrade CTA when exceeded
   - Link to billing page
6. ❌ **Storage Limits**
   - Track audio file storage per user
   - Delete old recordings after retention period
   - Pro: 90 days, Free: 30 days
7. ❌ **Quota Tests**
   - Verify enforcement logic
   - Test upgrade flows

---

## 📋 PHASE 5: LAUNCH PREP (16 remaining tasks)

**Goal:** Legal compliance, onboarding, email automation  
**Priority:** 🔴 CRITICAL - Required for public launch

### **5.1 Legal & Compliance (8 tasks)**

**Status:** Pages exist, GDPR service exists, need enforcement

**Tasks:**
1. ✅ **Legal Pages** (DONE - `templates/legal/`)
2. ✅ **GDPR Service** (DONE - `services/gdpr_compliance.py`)
3. ❌ **Cookie Consent Banner**
   - JS library (cookieconsent.js or custom)
   - Display on first visit
   - Categories: Essential, Analytics, Marketing
   - Store consent in localStorage + database
4. ❌ **ToS/Privacy Acceptance on Signup**
   - Checkbox on registration form
   - Link to legal pages
   - Store acceptance timestamp
5. ❌ **GDPR Data Export UI**
   - User settings: "Download My Data"
   - Generate ZIP (profile, sessions, transcripts)
   - Email download link
6. ❌ **GDPR Data Deletion UI**
   - User settings: "Delete My Account"
   - Confirmation modal with warnings
   - Soft delete (30-day grace period)
   - Purge all data after 30 days
7. ❌ **Data Retention Enforcement**
   - Background job to auto-delete old sessions
   - Notify users before deletion
   - Archive before purge
8. ❌ **Compliance Tests**
   - Cookie consent flow
   - Data export completeness
   - Data deletion verification

---

### **5.2 Email Automation (8 tasks)**

**Status:** SendGrid configured, need templates

**Tasks:**
1. ✅ **Email Service** (DONE - `services/email_service.py`)
2. ❌ **Welcome Email**
   - Trigger: User registration
   - Content: Welcome, quick start guide, resources
   - HTML template with Crown+ branding
3. ❌ **Email Verification**
   - Send verification link on signup
   - Verify endpoint: `/auth/verify/<token>`
   - Require verification to access features
4. ❌ **Password Reset Email**
   - Forgot password flow
   - Secure token generation
   - Time-limited reset link
5. ❌ **Billing Emails**
   - Payment successful
   - Payment failed (with retry info)
   - Subscription renewed
   - Trial expiring (7 days, 3 days, 1 day)
   - Invoice receipts
6. ❌ **Product Update Emails**
   - New feature announcements
   - Changelog digest
   - Admin: Create + schedule campaigns
7. ❌ **Engagement Emails**
   - Onboarding drip campaign (D1, D3, D7)
   - Re-engagement for inactive users
   - Usage milestone celebrations
8. ❌ **Email Template System**
   - Base template with Crown+ branding
   - Variable interpolation
   - Unsubscribe functionality
   - Preview before sending

---

## 📋 PHASE 6: COLLABORATION (11 remaining tasks)

**Goal:** Team features, real-time collaboration, notifications  
**Priority:** 🟠 HIGH - Enterprise value unlock

### **6.1 Team Management (5 tasks)**

**Status:** Models exist, stub routes exist, need UI

**Tasks:**
1. ✅ **Team Models** (DONE - `models/organization.py` + `models/core_models.py`)
2. ✅ **Team API Routes** (DONE - `routes/teams.py` stub)
3. ❌ **Team Creation UI**
   - Settings → Teams tab
   - Create team form (name, description)
   - Assign owner automatically
4. ❌ **Team Member Management UI**
   - List team members with roles
   - Invite by email
   - Accept/decline invitations
   - Remove members
   - Change roles (owner, admin, member)
5. ❌ **Team Permissions**
   - Owner: All permissions
   - Admin: Manage members, sessions
   - Member: View/edit sessions only
   - Middleware to enforce permissions

---

### **6.2 Real-Time Collaboration (6 tasks)**

**Status:** Not implemented

**Tasks:**
1. ❌ **Presence Indicators**
   - Show who's viewing a session (avatars)
   - Socket.IO presence tracking
   - Update on join/leave
2. ❌ **Live Edits Synchronization**
   - Broadcast segment edits to all viewers
   - Operational Transform or CRDT for conflict resolution
   - Show edit locks (who's editing)
3. ❌ **@Mentions System**
   - Parse @username in comments
   - Autocomplete team members
   - Send notification to mentioned user
4. ❌ **Notification Center**
   - Bell icon in navigation
   - List: Mentions, shares, task assignments
   - Mark as read
   - Real-time updates (Socket.IO)
5. ❌ **Shared Workspaces**
   - Workspace belongs to team
   - All sessions shared with team by default
   - Workspace settings (default permissions)
6. ❌ **Conflict Resolution**
   - Detect concurrent edits
   - Show conflict modal
   - Allow manual merge

---

## 📋 PHASE 7: ADMIN ADVANCED (19 remaining tasks)

**Goal:** Feature flags, A/B testing, incident management  
**Priority:** 🟡 MEDIUM - Production operations

### **7.1 Feature Flags (5 tasks)**

**Status:** Models + API exist, need UI

**Tasks:**
1. ✅ **Feature Flag Models** (DONE - `models/core_models.py`)
2. ✅ **Feature Flag API** (DONE - `routes/flags.py`)
3. ❌ **Feature Flag Dashboard UI**
   - Admin → Feature Flags page
   - List all flags (key, enabled, note)
   - Toggle on/off
   - Edit notes
4. ❌ **Flag Creation Form**
   - Create new flag
   - Set default state
   - Add description
5. ❌ **Frontend Flag Integration**
   - JS service to check flags
   - Conditionally render features
   - Cache flags in localStorage

---

### **7.2 A/B Testing (6 tasks)**

**Status:** Not implemented

**Tasks:**
1. ❌ **Experiment Model**
   - name, variants (A/B/C), allocation (50/50)
   - start_date, end_date, status
2. ❌ **Experiment Assignment**
   - Assign user to variant (deterministic hash)
   - Store in session/cookie
   - Track variant in analytics
3. ❌ **Experiment Dashboard**
   - Create experiment form
   - View results (conversion by variant)
   - Statistical significance calculator
4. ❌ **Event Tracking**
   - Track conversion events
   - Link to experiment variant
   - Store in ExperimentEvent table
5. ❌ **Results Visualization**
   - Chart.js comparison
   - Confidence intervals
   - Recommend winner
6. ❌ **Gradual Rollout**
   - 0% → 10% → 50% → 100% rollout slider
   - Automatically assign users
   - Monitor for errors

---

### **7.3 Incident Management (8 tasks)**

**Status:** Not implemented

**Tasks:**
1. ❌ **Incident Model**
   - title, description, severity, status, assigned_to
   - created_at, resolved_at
2. ❌ **Incident Dashboard**
   - List open incidents
   - Create incident form
   - Assign to admin user
   - Status: Open → Investigating → Resolved
3. ❌ **Alerting Integration**
   - Trigger incident on error spike (Sentry)
   - Auto-create from health check failures
   - PagerDuty/Slack webhooks
4. ❌ **Incident Timeline**
   - Log of actions taken
   - Comments from team
   - Resolution notes
5. ❌ **Post-Mortem Template**
   - Auto-generate from incident
   - Sections: Impact, Root Cause, Fix, Prevention
   - Store as document
6. ❌ **Status Page**
   - Public page showing system status
   - Manual incident updates
   - Uptime history
7. ❌ **On-Call Schedule**
   - Assign on-call admin per week
   - Rotation calendar
   - Notification routing
8. ❌ **Runbook Library**
   - Common issues + resolution steps
   - Link from incident dashboard
   - Admin: Create/edit runbooks

---

## 📋 PHASE 8: SCALE & POLISH (8 remaining tasks)

**Goal:** Performance optimization, accessibility, final polish  
**Priority:** 🟢 NORMAL - Quality improvements

### **8.1 Performance (4 tasks)**

**Tasks:**
1. ❌ **Frontend Code Splitting**
   - Lazy load routes (dashboard, copilot, settings)
   - Dynamic imports for heavy components
   - Webpack/Vite optimization
2. ❌ **Image Optimization**
   - Convert to WebP format
   - Responsive images (srcset)
   - Lazy loading
   - Compress with ImageOptim
3. ❌ **Bundle Size Optimization**
   - Tree shaking
   - Remove unused JS (130+ files cleanup)
   - Minify CSS/JS
   - Target: <500KB total bundle
4. ❌ **Caching Strategy**
   - Service worker for offline support
   - Cache static assets (1 year)
   - Versioned filenames

---

### **8.2 Accessibility & Polish (4 tasks)**

**Tasks:**
1. ❌ **Comprehensive Accessibility Audit**
   - Run Lighthouse accessibility score
   - Manual testing with screen reader
   - Keyboard navigation verification
   - Color contrast check
   - Target: WCAG 2.1 AA compliance
2. ❌ **Cross-Browser Testing**
   - Chrome, Firefox, Safari, Edge
   - Automated Playwright tests
   - Fix browser-specific bugs
3. ❌ **Mobile Optimization**
   - Test on real devices (iOS, Android)
   - Touch target sizes (44x44px minimum)
   - Mobile-specific gestures
   - PWA manifest
4. ❌ **Copy & Microcopy Polish**
   - Review all UI text
   - Error messages clarity
   - Empty states
   - Success confirmations
   - Help tooltips

---

## 🎯 IMPLEMENTATION SEQUENCE

**Recommended order for systematic completion:**

### **Sprint 1: Billing Foundation (2-3 weeks)**
- Phase 4.1: Billing System (all 10 tasks)
- Get Stripe checkout working
- Enforce usage limits

### **Sprint 2: Admin Tools (3-4 weeks)**
- Phase 4.2: Admin Dashboard (tasks 1-7)
- Phase 4.3: Limits & Quotas (all 7 tasks)
- Build user management, metrics

### **Sprint 3: Legal & Email (2 weeks)**
- Phase 5.1: Legal & Compliance (all 8 tasks)
- Phase 5.2: Email Automation (all 8 tasks)
- GDPR enforcement, email templates

### **Sprint 4: Team Features (2-3 weeks)**
- Phase 6.1: Team Management (all 5 tasks)
- Phase 6.2: Real-Time Collaboration (all 6 tasks)
- Build team UI, presence, notifications

### **Sprint 5: Advanced Admin (2 weeks)**
- Phase 7.1: Feature Flags (all 5 tasks)
- Phase 7.2: A/B Testing (all 6 tasks)
- Phase 7.3: Incident Management (all 8 tasks)

### **Sprint 6: Polish & Launch (1-2 weeks)**
- Phase 8.1: Performance (all 4 tasks)
- Phase 8.2: Accessibility & Polish (all 4 tasks)
- Final QA, launch checklist

**Total Estimated Time: 12-17 weeks (3-4 months)**

---

## 🚨 CRITICAL PATH

**These tasks MUST be done before public launch:**

1. ✅ Billing System (Phase 4.1) - Revenue model
2. ✅ Admin Dashboard (Phase 4.2) - Operations
3. ✅ Usage Limits (Phase 4.3) - Cost control
4. ✅ Legal Compliance (Phase 5.1) - Risk mitigation
5. ✅ Email Automation (Phase 5.2) - User engagement
6. ⚠️ Team Management (Phase 6.1) - Enterprise value
7. ⚠️ Feature Flags (Phase 7.1) - Safe rollouts

**Everything else can be post-launch improvements.**

---

## 📝 TESTING STRATEGY

For each phase:
1. **Unit tests** for services and models
2. **Integration tests** for API endpoints
3. **E2E tests** for critical user flows
4. **Manual QA** before marking complete

**Final comprehensive test suite** after all 268 tasks.

---

## ✅ SUCCESS CRITERIA

**Phase 4 Complete:**
- ✅ Can charge customers via Stripe
- ✅ Admin can manage users and view metrics
- ✅ Usage limits enforced automatically

**Phase 5 Complete:**
- ✅ GDPR compliance verified (data export/deletion)
- ✅ All email templates working
- ✅ Legal acceptance on signup

**Phase 6 Complete:**
- ✅ Teams can collaborate in real-time
- ✅ Notification center functional
- ✅ Presence indicators working

**Phases 7-8 Complete:**
- ✅ Feature flags control releases
- ✅ A/B tests can run
- ✅ Performance: Lighthouse score >90
- ✅ Accessibility: WCAG 2.1 AA

---

## 🎉 LAUNCH READINESS

**When all 268 tasks complete:**
- Production-ready SaaS platform
- Revenue-generating billing system
- Enterprise-grade collaboration
- Full legal compliance
- Scalable infrastructure
- Premium user experience

**Mina will be ready to onboard paying customers and scale to thousands of users.**
