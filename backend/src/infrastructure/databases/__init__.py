from infrastructure.databases.mssql import init_mssql
from infrastructure.models import appointment_model, ai_job, ai_summary, assessment_item, audit_log, clo_plo_map, clo, department, feedback, notification, permission, plo, program, review_comment, review_round, role_permission, role, subject_relation, subject, subscription, syllabus_section, syllabus_version, syllabus, system_setting, todo_model, user_model, user_role, user, workflow_action  

def init_db(app):
    init_mssql(app)
    
from infrastructure.databases.mssql import Base