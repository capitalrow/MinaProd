"""
Mina Backup Scheduler Service
Application-level backup scheduling using APScheduler
Works on Replit and other platforms without cron
"""

import os
import subprocess
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Manages automated database backups using APScheduler
    """
    
    def __init__(self, app=None):
        self.scheduler = None
        self.app = app
        self.backup_script_path = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Get backup script path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_script_path = os.path.join(base_dir, 'scripts', 'backup_database.sh')
        
        # Check if backup script exists
        if not os.path.exists(self.backup_script_path):
            logger.warning(f"Backup script not found: {self.backup_script_path}")
            return
        
        # Get backup configuration from app config
        self.backup_enabled = app.config.get('BACKUP_ENABLED', True)
        self.backup_schedule = app.config.get('BACKUP_SCHEDULE', 'daily')  # daily, hourly, or cron expression
        self.backup_hour = app.config.get('BACKUP_HOUR', 2)  # Default: 2 AM
        
        # Initialize scheduler if enabled
        if self.backup_enabled:
            self._init_scheduler()
    
    def _init_scheduler(self):
        """Initialize APScheduler"""
        self.scheduler = BackgroundScheduler(daemon=True)
        
        # Configure backup job based on schedule
        if self.backup_schedule == 'daily':
            # Daily backup at specified hour
            trigger = CronTrigger(hour=self.backup_hour, minute=0)
            logger.info(f"Backup scheduled: Daily at {self.backup_hour}:00")
        elif self.backup_schedule == 'hourly':
            # Hourly backups
            trigger = CronTrigger(minute=0)
            logger.info("Backup scheduled: Hourly")
        elif self.backup_schedule.startswith('cron:'):
            # Custom cron expression
            cron_expr = self.backup_schedule.replace('cron:', '')
            trigger = CronTrigger.from_crontab(cron_expr)
            logger.info(f"Backup scheduled: {cron_expr}")
        else:
            logger.warning(f"Invalid backup schedule: {self.backup_schedule}")
            return
        
        # Add backup job to scheduler
        self.scheduler.add_job(
            func=self._run_backup,
            trigger=trigger,
            id='database_backup',
            name='Database Backup',
            replace_existing=True,
            max_instances=1  # Prevent concurrent backups
        )
        
        logger.info("Backup scheduler initialized")
    
    def _run_backup(self):
        """Execute backup script"""
        logger.info("Starting scheduled database backup...")
        
        try:
            # Run backup script
            result = subprocess.run(
                [self.backup_script_path],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                env=os.environ.copy()
            )
            
            if result.returncode == 0:
                logger.info("Backup completed successfully")
                logger.debug(f"Backup output: {result.stdout}")
                
                # Send success notification if configured
                self._send_notification('success', result.stdout)
            else:
                logger.error(f"Backup failed with exit code {result.returncode}")
                logger.error(f"Backup error: {result.stderr}")
                
                # Send failure notification
                self._send_notification('failure', result.stderr)
        
        except subprocess.TimeoutExpired:
            logger.error("Backup script timed out after 10 minutes")
            self._send_notification('failure', 'Backup timed out')
        
        except Exception as e:
            logger.error(f"Backup failed with exception: {str(e)}")
            self._send_notification('failure', str(e))
    
    def _send_notification(self, status, message):
        """Send backup status notification (placeholder for future notification integration)"""
        # TODO: Integrate with notification service (email, Slack, etc.)
        if status == 'failure':
            logger.error(f"Backup notification: {status} - {message}")
        else:
            logger.info(f"Backup notification: {status}")
    
    def start(self):
        """Start the backup scheduler"""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Backup scheduler started")
            return True
        return False
    
    def stop(self):
        """Stop the backup scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Backup scheduler stopped")
            return True
        return False
    
    def trigger_backup_now(self):
        """Manually trigger an immediate backup"""
        logger.info("Manual backup triggered")
        self._run_backup()
    
    def get_next_run_time(self):
        """Get the next scheduled backup time"""
        if not self.scheduler:
            return None
        
        job = self.scheduler.get_job('database_backup')
        if job and job.next_run_time:
            return job.next_run_time
        return None
    
    def get_status(self):
        """Get backup scheduler status"""
        if not self.scheduler:
            return {
                'enabled': False,
                'running': False,
                'next_run': None
            }
        
        next_run = self.get_next_run_time()
        
        return {
            'enabled': self.backup_enabled,
            'running': self.scheduler.running,
            'schedule': self.backup_schedule,
            'next_run': next_run.isoformat() if next_run else None,
            'next_run_human': next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'Not scheduled'
        }


# Global backup scheduler instance
backup_scheduler = BackupScheduler()


def init_backup_scheduler(app):
    """
    Initialize backup scheduler with Flask app
    Call this from app initialization
    """
    backup_scheduler.init_app(app)
    backup_scheduler.start()
    
    # Register cleanup on app teardown
    @app.teardown_appcontext
    def shutdown_backup_scheduler(exception=None):
        backup_scheduler.stop()
    
    return backup_scheduler
