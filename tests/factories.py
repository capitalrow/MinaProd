"""
Test data factories using factory_boy and faker.
"""
import factory
from factory import Faker, LazyAttribute, SubFactory
from faker import Faker as FakerInstance
from datetime import datetime, timedelta
import random

fake = FakerInstance()

class UserFactory(factory.Factory):
    """Factory for creating test users."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYOLxdU5aZm'  # 'password123'
    created_at = LazyAttribute(lambda _: fake.date_time_this_year())
    is_active = True
    is_admin = False

class SessionFactory(factory.Factory):
    """Factory for creating test sessions."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: f'session_{n}')
    user_id = factory.Sequence(lambda n: n + 1)
    title = LazyAttribute(lambda _: fake.catch_phrase())
    status = factory.LazyAttribute(lambda _: random.choice(['active', 'paused', 'completed']))
    created_at = LazyAttribute(lambda _: fake.date_time_this_month())
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(minutes=random.randint(1, 120)))
    duration = LazyAttribute(lambda _: random.randint(60, 3600))
    word_count = LazyAttribute(lambda _: random.randint(100, 5000))
    speaker_count = LazyAttribute(lambda _: random.randint(1, 10))
    language = 'en'
    model = 'whisper-1'
    
class SegmentFactory(factory.Factory):
    """Factory for creating transcription segments."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    session_id = factory.Sequence(lambda n: f'session_{n}')
    text = LazyAttribute(lambda _: fake.sentence(nb_words=10))
    confidence = LazyAttribute(lambda _: round(random.uniform(0.8, 1.0), 3))
    start_time = LazyAttribute(lambda _: round(random.uniform(0, 60), 2))
    end_time = LazyAttribute(lambda obj: round(obj.start_time + random.uniform(1, 5), 2))
    speaker_id = LazyAttribute(lambda _: f'speaker_{random.randint(0, 3)}')
    is_final = True
    created_at = LazyAttribute(lambda _: fake.date_time_this_month())
    
class MeetingFactory(factory.Factory):
    """Factory for creating meetings."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1)
    title = LazyAttribute(lambda _: f'{fake.company()} - {fake.catch_phrase()}')
    description = LazyAttribute(lambda _: fake.paragraph())
    status = factory.LazyAttribute(lambda _: random.choice(['scheduled', 'live', 'completed', 'cancelled']))
    scheduled_at = LazyAttribute(lambda _: fake.future_datetime(end_date='+30d'))
    started_at = None
    ended_at = None
    duration_minutes = LazyAttribute(lambda _: random.choice([30, 60, 90, 120]))
    participant_count = LazyAttribute(lambda _: random.randint(2, 15))
    recording_url = None
    transcript_status = 'pending'
    
class SummaryFactory(factory.Factory):
    """Factory for creating meeting summaries."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    session_id = factory.Sequence(lambda n: f'session_{n}')
    summary_text = LazyAttribute(lambda _: fake.paragraph(nb_sentences=5))
    key_points = LazyAttribute(lambda _: [fake.sentence() for _ in range(3)])
    action_items = LazyAttribute(lambda _: [fake.sentence() for _ in range(random.randint(1, 5))])
    participants = LazyAttribute(lambda _: [fake.name() for _ in range(random.randint(2, 8))])
    created_at = LazyAttribute(lambda _: fake.date_time_this_month())
    model_used = 'gpt-4'
    
class TaskFactory(factory.Factory):
    """Factory for creating action items/tasks."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    session_id = factory.Sequence(lambda n: f'session_{n}')
    title = LazyAttribute(lambda _: fake.sentence(nb_words=6))
    description = LazyAttribute(lambda _: fake.paragraph())
    assignee = LazyAttribute(lambda _: fake.name())
    due_date = LazyAttribute(lambda _: fake.future_date(end_date='+14d'))
    status = factory.LazyAttribute(lambda _: random.choice(['pending', 'in_progress', 'completed', 'cancelled']))
    priority = factory.LazyAttribute(lambda _: random.choice(['low', 'medium', 'high']))
    created_at = LazyAttribute(lambda _: fake.date_time_this_month())

class WorkspaceFactory(factory.Factory):
    """Factory for creating workspaces."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    name = LazyAttribute(lambda _: f'{fake.company()} Workspace')
    slug = LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    owner_id = factory.Sequence(lambda n: n + 1)
    member_count = LazyAttribute(lambda _: random.randint(1, 50))
    plan = factory.LazyAttribute(lambda _: random.choice(['free', 'pro', 'enterprise']))
    created_at = LazyAttribute(lambda _: fake.date_time_this_year())
    is_active = True

class ParticipantFactory(factory.Factory):
    """Factory for creating meeting participants."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    meeting_id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1)
    name = LazyAttribute(lambda _: fake.name())
    email = LazyAttribute(lambda obj: f'{obj.name.lower().replace(" ", ".")}@example.com')
    role = factory.LazyAttribute(lambda _: random.choice(['organizer', 'presenter', 'attendee']))
    status = factory.LazyAttribute(lambda _: random.choice(['invited', 'accepted', 'declined', 'attended']))
    joined_at = LazyAttribute(lambda _: fake.date_time_this_month())
    left_at = None
    duration_minutes = LazyAttribute(lambda _: random.randint(5, 120))

# Batch creation helpers
def create_user_batch(count=10):
    """Create multiple users."""
    return [UserFactory() for _ in range(count)]

def create_session_batch(count=10, user_id=1):
    """Create multiple sessions for a user."""
    return [SessionFactory(user_id=user_id) for _ in range(count)]

def create_segment_batch(count=20, session_id='session_1'):
    """Create multiple segments for a session."""
    return [SegmentFactory(session_id=session_id) for _ in range(count)]

def create_participant_batch(count=5, meeting_id=1):
    """Create multiple participants for a meeting."""
    return [ParticipantFactory(meeting_id=meeting_id) for _ in range(count)]

def create_complete_meeting_data():
    """Create a complete meeting with all related data."""
    user = UserFactory()
    session = SessionFactory(user_id=user['id'])
    segments = create_segment_batch(count=15, session_id=session['id'])
    summary = SummaryFactory(session_id=session['id'])
    tasks = [TaskFactory(session_id=session['id']) for _ in range(3)]
    
    return {
        'user': user,
        'session': session,
        'segments': segments,
        'summary': summary,
        'tasks': tasks
    }
