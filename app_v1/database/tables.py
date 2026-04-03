from enum import Enum


class DatabaseTables(Enum):
    "Tables names in database"
    COMPANY_TABLE = 'companies'
    USER_TABLE = 'users'
    JOB_TABLE = 'jobs'
    JOB_NOTIFICATION_TARGETS_TABLE = 'job_notification_targets'
    USER_QUOTA_TABLE = 'user_quota'