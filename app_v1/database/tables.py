from enum import Enum


class DatabaseTables(Enum):
    "Tables names in database"
    COMPANY_TABLE = 'companies'
    USER_TABLE = 'users'
    JOB_NOTIFICATION_TARGETS_TABLE = 'job_notification_targets'