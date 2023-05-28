import sys
from pathlib import Path

src_path = str(Path(__file__).parent / 'src')
try:
    sys.path.index(src_path)
except ValueError:
    sys.path.append(src_path)

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
