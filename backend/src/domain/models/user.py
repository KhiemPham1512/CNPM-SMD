from datetime import datetime


class User:
    def __init__(self, user_id: int = None, username: str = None, password_hash: str = None, 
                 full_name: str = None, email: str = None, status: str = None, 
                 created_at: datetime = None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.email = email
        self.status = status
        self.created_at = created_at