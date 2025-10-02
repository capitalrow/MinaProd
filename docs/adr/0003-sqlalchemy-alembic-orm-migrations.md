# 3. SQLAlchemy ORM with Alembic Migrations

**Date**: 2025-10-02

**Status**: Accepted

**Context**: We needed a robust data access layer that provides type safety, prevents SQL injection, and supports safe database schema evolution across development and production environments.

**Decision**: Use SQLAlchemy as the ORM and Alembic for database migrations, integrated via Flask-SQLAlchemy.

**Alternatives Considered**:
- Raw SQL: More control but prone to SQL injection and harder to maintain
- Drizzle ORM: TypeScript-focused, not suitable for Python backend
- Peewee: Simpler but less feature-rich than SQLAlchemy

**Consequences**:
- **Positive**:
  - Type-safe database operations
  - Automatic SQL injection prevention
  - Support for complex relationships and eager loading
  - Alembic provides version-controlled schema migrations
  - Flask-SQLAlchemy integration with application context
  - Connection pooling and query optimization
  
- **Negative**:
  - Learning curve for complex queries
  - N+1 query problems require careful optimization
  - Migration files require code review
