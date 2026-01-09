from datetime import datetime


class Syllabus:
    def __init__(self, syllabus_id: int = None, subject_id: int = None, 
                 program_id: int = None, owner_lecturer_id: int = None,
                 current_version_id: int = None, lifecycle_status: str = None,
                 created_at: datetime = None):
        self.syllabus_id = syllabus_id
        self.subject_id = subject_id
        self.program_id = program_id
        self.owner_lecturer_id = owner_lecturer_id
        self.current_version_id = current_version_id
        self.lifecycle_status = lifecycle_status
        self.created_at = created_at

