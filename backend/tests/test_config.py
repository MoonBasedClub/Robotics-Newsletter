from app.config import Settings


def test_database_url_accepts_supabase_ssl_query_params():
    url = "postgresql+psycopg://user:password@example.supabase.co:6543/postgres?sslmode=require"

    settings = Settings(DATABASE_URL=url)

    assert settings.database_url == url


def test_database_url_adds_psycopg_driver_to_plain_postgresql_urls():
    settings = Settings(DATABASE_URL="postgresql://user:password@example.supabase.co:6543/postgres?sslmode=require")

    assert (
        settings.database_url
        == "postgresql+psycopg://user:password@example.supabase.co:6543/postgres?sslmode=require"
    )


def test_database_url_adds_psycopg_driver_to_legacy_postgres_urls():
    settings = Settings(DATABASE_URL="postgres://user:password@example.supabase.co:6543/postgres?sslmode=require")

    assert (
        settings.database_url
        == "postgresql+psycopg://user:password@example.supabase.co:6543/postgres?sslmode=require"
    )
