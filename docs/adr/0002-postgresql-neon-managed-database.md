# 2. PostgreSQL (Neon Managed) for Production Database

**Date**: 2025-10-02

**Status**: Accepted

**Context**: Mina requires a production-grade relational database that supports ACID transactions, complex queries, and JSON data types for storing meeting metadata, transcripts, and analytics.

**Decision**: Use PostgreSQL (Neon managed service) as the primary database, with SQLAlchemy ORM and Alembic for migrations.

**Alternatives Considered**:
- MongoDB: NoSQL but sacrifices ACID guarantees and complex joins
- MySQL: Less robust JSON support and PostgreSQL-specific features
- SQLite: Development only, not suitable for production concurrent writes

**Consequences**:
- **Positive**:
  - ACID compliance ensures data integrity
  - Advanced indexing (composite, partial, GIN for JSON)
  - Full-text search capabilities
  - Robust JSON/JSONB support for flexible schemas
  - Neon provides automatic backups, point-in-time recovery
  - Serverless scaling with Neon
  - Connection pooling and performance optimization
  
- **Negative**:
  - More complex than NoSQL for simple key-value operations
  - Requires careful index management for query performance
  - Migration management requires discipline
