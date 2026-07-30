from src.config import settings
from src.tools.database import DBTool


def main():
    result = DBTool(settings.DB_PATH, allow_writes=True).seed_demo_data()
    print(result)


if __name__ == "__main__":
    main()
