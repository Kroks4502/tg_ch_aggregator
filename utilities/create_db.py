from models import (Category, Source, Filter, Admin,
                    FilterMessageHistory, CategoryMessageHistory)
from settings import DATABASE

DATABASE.create_tables(
    [
        Category, Source, Filter, Admin,
        FilterMessageHistory, CategoryMessageHistory
    ]
)
