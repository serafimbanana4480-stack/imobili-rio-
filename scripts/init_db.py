"""Initialize database tables."""
from realestate_engine.database.models import init_db
from realestate_engine.utils.config import config

init_db(config.database_url)
print('Database initialized')
