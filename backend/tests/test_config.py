from app.config import Settings


def test_database_url_accepts_supabase_ssl_query_params():
    url = "postgresql+psycopg://user:password@example.supabase.co:6543/postgres?sslmode=require"

    settings = Settings(DATABASE_URL=url)

    assert settings.database_url == url
