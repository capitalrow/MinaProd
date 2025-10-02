# Analytics Strategy

## Analytics Tool Selection (T0.37)

### Chosen Approach: Hybrid Analytics Stack

**Primary Solution**: Custom event tracking with optional third-party integrations

**Rationale**:
1. **Data Ownership**: Keep sensitive meeting data in our database
2. **Flexibility**: Custom metrics specific to meeting analytics
3. **Cost**: Avoid per-event pricing for high-volume transcription events
4. **Privacy**: GDPR/CCPA compliance easier with self-hosted
5. **Integration Ready**: Can add Mixpanel/Amplitude later

### Analytics Stack Components

1. **Custom Event Tracking** (Primary)
   - PostgreSQL for event storage
   - Python service for event collection
   - Real-time dashboard for product team
   
2. **Performance Monitoring** (Implemented)
   - Sentry for error tracking and APM
   - Custom performance monitoring service
   
3. **Optional Integrations** (Future)
   - Mixpanel: User journey analytics
   - Amplitude: Cohort analysis
   - PostHog: Self-hosted alternative

## Key Metrics Framework

### Activation Metrics (T0.39)
User has completed first meaningful action

**Activation Events**:
- First meeting created
- First transcription session started
- First task created from meeting
- Team member invited

**Activation Definition**: User who completes first transcription session within 7 days of signup

**Target**: 60% activation rate

### Engagement Metrics (T0.40)
User regularly uses core features

**Daily Active Users (DAU)**:
- Started transcription session
- Created/updated task
- Viewed meeting dashboard

**Weekly Active Users (WAU)**:
- At least 2 meetings per week
- Task completion rate

**Engagement Score** (0-100):
- Meeting frequency: 30 points
- Task creation: 25 points
- Collaboration (sharing): 20 points
- Feature adoption: 25 points

**Target**: DAU/MAU ratio > 40%

### Retention Metrics (T0.41)
Users continue using product over time

**Retention Cohorts**:
- Day 1, Day 7, Day 30, Day 90

**Retention Definition**: User started at least one meeting in period

**Retention Triggers**:
- Email reminders for pending tasks
- Weekly summary of meetings
- Collaboration notifications

**Target**: 70% Day 7, 50% Day 30

### Conversion Funnel (T0.42)
Free → Paid conversion journey

**Funnel Stages**:
1. Sign up (100%)
2. Email verified (80%)
3. First meeting (60%)
4. Team invite sent (40%)
5. Workspace upgraded (10%)

**Conversion Events**:
- Trial started
- Billing info added
- Upgrade clicked
- Payment completed

**Target**: 10% free-to-paid conversion

## Event Taxonomy

### User Events
- `user.signup`
- `user.login`
- `user.logout`
- `user.profile_updated`
- `user.settings_changed`

### Meeting Events
- `meeting.created`
- `meeting.started`
- `meeting.completed`
- `meeting.cancelled`
- `meeting.shared`

### Session Events
- `session.started`
- `session.audio_received`
- `session.transcription_received`
- `session.ended`
- `session.error`

### Task Events
- `task.created`
- `task.assigned`
- `task.status_changed`
- `task.completed`
- `task.overdue`

### Analytics Events
- `analytics.generated`
- `analytics.viewed`
- `analytics.exported`

### Collaboration Events
- `workspace.member_invited`
- `workspace.member_joined`
- `meeting.participant_added`

## A/B Testing Framework (T0.43)

### Feature Flags
```python
def is_feature_enabled(user_id, feature_name):
    # Consistent bucketing based on user_id
    bucket = hash(f"{user_id}_{feature_name}") % 100
    
    feature_rollout = {
        'new_ai_summary': 50,  # 50% rollout
        'advanced_analytics': 100,  # 100% rollout
        'collaboration_v2': 0,  # Disabled
    }
    
    return bucket < feature_rollout.get(feature_name, 0)
```

### Test Variants
- **Control**: Current experience
- **Variant A**: Test hypothesis
- **Variant B**: Alternative hypothesis

### Success Criteria
- Statistical significance (p < 0.05)
- Minimum sample size: 1000 users per variant
- Test duration: 2 weeks minimum

## Session Replay (T0.44)

### Implementation Options

**Option 1**: Self-hosted (Recommended)
- Library: rrweb (open source)
- Storage: PostgreSQL + object storage
- Privacy: Full control, GDPR compliant

**Option 2**: Third-party
- PostHog (self-hosted option available)
- LogRocket
- FullStory

### Privacy Considerations
- Redact sensitive data (passwords, API keys)
- Opt-out for users
- 30-day retention
- Encrypted storage

### Use Cases
- Bug reproduction
- UX improvement
- Support tickets
- User behavior analysis

## Product Analytics Dashboard (T0.45)

### Dashboard Metrics

**Overview**:
- Total users (active, inactive)
- DAU/WAU/MAU
- Activation rate
- Retention cohorts

**Engagement**:
- Meeting creation trend
- Average meetings per user
- Task completion rate
- Session duration

**Conversion**:
- Funnel visualization
- Drop-off points
- Time to upgrade
- Revenue metrics

**Feature Adoption**:
- Feature usage %
- New feature adoption rate
- Power user identification

### Refresh Rate
- Real-time: Critical metrics (errors, active sessions)
- Hourly: User engagement
- Daily: Retention, conversion

## Data Privacy & Compliance

### GDPR Compliance
- User data export
- Right to deletion
- Consent management
- Data minimization

### Data Retention
- Events: 2 years
- Session replays: 30 days
- Personal data: Until account deletion
- Anonymized analytics: Indefinite

### Security
- Encrypt events in transit (HTTPS)
- Encrypt events at rest (database encryption)
- Access control for analytics dashboard
- Audit log for data access
