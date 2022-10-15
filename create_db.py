from models import (BaseModel, Category, Source, Filter, Admin,
                    FilterMessageHistory, CategoryMessageHistory)


BaseModel._meta.database.create_tables(
    [
        Category, Source, Filter, Admin,
        FilterMessageHistory, CategoryMessageHistory
    ]
)
