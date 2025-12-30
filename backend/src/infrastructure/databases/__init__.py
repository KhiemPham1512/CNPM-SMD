from infrastructure.databases.mssql import init_mssql
from infrastructure.models import appointment_model

def init_db(app):
    init_mssql(app)
    
from infrastructure.databases.mssql import Base