from config import DATABASE, configure_logging
from models import (
    Admin,
    Category,
    CategoryMessageHistory,
    Filter,
    FilterMessageHistory,
    Source,
)

if __name__ == '__main__':
    configure_logging()
    DATABASE.create_tables(
        [Category, Source, Filter, Admin, FilterMessageHistory, CategoryMessageHistory]
    )
