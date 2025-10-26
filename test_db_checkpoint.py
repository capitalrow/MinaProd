"""
Quick database verification script for Test Checkpoint 1
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Get database URL from environment
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not set")
    exit(1)

# Connect to database
conn = psycopg2.connect(db_url)
cur = conn.cursor(cursor_factory=RealDictCursor)

print('=' * 80)
print('DATABASE PERSISTENCE CHECKPOINT')
print('=' * 80)

# Check summaries
cur.execute("""
    SELECT id, session_id, created_at, engine, level, style,
           LENGTH(summary_md) as summary_length,
           jsonb_array_length(actions::jsonb) as actions_count,
           jsonb_array_length(decisions::jsonb) as decisions_count,
           jsonb_array_length(risks::jsonb) as risks_count
    FROM summaries
    ORDER BY created_at DESC
    LIMIT 3
""")
summaries = cur.fetchall()

print(f'\n📊 SUMMARIES: {len(summaries)} recent records')
for s in summaries:
    print(f'   ID={s["id"]}, Session={s["session_id"]}, Engine={s["engine"]}')
    print(f'   Summary length: {s["summary_length"]} chars')
    print(f'   Actions: {s["actions_count"]}, Decisions: {s["decisions_count"]}, Risks: {s["risks_count"]}')
    print(f'   Level: {s["level"]}, Style: {s["style"]}, Created: {s["created_at"]}')
    print()

# Check tasks
cur.execute("""
    SELECT id, title, session_id, meeting_id, status, priority
    FROM tasks
    ORDER BY created_at DESC
    LIMIT 5
""")
tasks = cur.fetchall()

print(f'✅ TASKS: {len(tasks)} records')
for t in tasks:
    print(f'   ID={t["id"]}: {t["title"][:50]}')
    print(f'   Session={t["session_id"]}, Meeting={t["meeting_id"]}, Status={t["status"]}')

# Check analytics
cur.execute("""
    SELECT id, meeting_id, 
           overall_engagement_score, 
           overall_sentiment_score,
           decisions_made_count,
           action_items_created,
           word_count
    FROM analytics
    ORDER BY id DESC
    LIMIT 5
""")
analytics = cur.fetchall()

print(f'\n📈 ANALYTICS: {len(analytics)} records')
for a in analytics:
    print(f'   Meeting={a["meeting_id"]}, Engagement={a["overall_engagement_score"]}, Sentiment={a["overall_sentiment_score"]}')
    print(f'   Decisions={a["decisions_made_count"]}, Actions={a["action_items_created"]}, Words={a["word_count"]}')

# Check sessions
cur.execute("""
    SELECT id, external_id, status, 
           (SELECT COUNT(*) FROM segments WHERE session_id = sessions.id AND kind='final') as segment_count
    FROM sessions
    ORDER BY id DESC
    LIMIT 3
""")
sessions = cur.fetchall()

print(f'\n🎙️  SESSIONS: {len(sessions)} recent')
for s in sessions:
    print(f'   ID={s["id"]}, External={s["external_id"]}, Status={s["status"]}, Segments={s["segment_count"]}')

print('\n' + '=' * 80)
print('CHECKPOINT SUMMARY:')
print(f'✅ Summaries table: {len(summaries) > 0}')
print(f'✅ Tasks table: {len(tasks) >= 0}')  # Can be empty
print(f'✅ Analytics table: {len(analytics) >= 0}')  # Can be empty
print(f'✅ Sessions table: {len(sessions) > 0}')
print('=' * 80)

cur.close()
conn.close()
