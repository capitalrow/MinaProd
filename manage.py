# manage.py
"""
Flask CLI entrypoint used by Alembic (flask db ...).

Keep it tiny:
- import the app/db singletons
- import models so Alembic can autogenerate
"""

# IMPORTANT: ensure MINA_CLI is set *before* this module is imported by flask
# You do that in the shell:   export MINA_CLI=1

from app_refactored import app, db  # noqa: F401  (app exposed to Flask CLI)
import models  # noqa: F401  (side-effect: registers models with SQLAlchemy)