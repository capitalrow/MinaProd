"""
Application Performance Monitoring (APM) integration.
Integrates with external APM tools like Sentry Performance, New Relic, etc.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class APMIntegration:
    """Integration with APM platforms."""
    
    def __init__(self):
        self.sentry_enabled = self._check_sentry()
        self.initialized = False
    
    def _check_sentry(self) -> bool:
        """Check if Sentry is configured."""
        return bool(os.environ.get('SENTRY_DSN'))
    
    def initialize(self, app):
        """Initialize APM integrations."""
        if self.sentry_enabled:
            self._initialize_sentry_performance(app)
        
        self.initialized = True
        logger.info(f"APM initialized (Sentry: {self.sentry_enabled})")
    
    def _initialize_sentry_performance(self, app):
        """Initialize Sentry Performance Monitoring."""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            
            sentry_dsn = os.environ.get('SENTRY_DSN')
            environment = os.environ.get('FLASK_ENV', 'production')
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=0.1 if environment == 'production' else 1.0,
                profiles_sample_rate=0.1 if environment == 'production' else 1.0,
                environment=environment,
                send_default_pii=False
            )
            
            logger.info("Sentry Performance Monitoring initialized")
            
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry Performance")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry Performance: {e}")
    
    def start_transaction(self, name: str, op: str):
        """Start a performance transaction."""
        if self.sentry_enabled:
            try:
                import sentry_sdk
                return sentry_sdk.start_transaction(name=name, op=op)
            except Exception as e:
                logger.debug(f"Failed to start transaction: {e}")
        
        return None
    
    def set_tag(self, key: str, value: str):
        """Set a tag for the current transaction."""
        if self.sentry_enabled:
            try:
                import sentry_sdk
                sentry_sdk.set_tag(key, value)
            except Exception as e:
                logger.debug(f"Failed to set tag: {e}")
    
    def set_context(self, name: str, context: dict):
        """Set context for the current transaction."""
        if self.sentry_enabled:
            try:
                import sentry_sdk
                sentry_sdk.set_context(name, context)
            except Exception as e:
                logger.debug(f"Failed to set context: {e}")


apm_integration = APMIntegration()
