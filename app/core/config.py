from pydantic import BaseSettings

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    SQLALCHEMY_DATABASE_TEST_URI: str = "sqlite:///:memory:"
    SECRET_KEY: str = "test-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    @property
    def get_database_url(self) -> str:
        return self.SQLALCHEMY_DATABASE_URI

settings = Settings() 