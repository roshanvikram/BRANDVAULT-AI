"""G — config portability + CORS hardening checks (verifiable offline)."""
import unittest

from backend.app.core.config import _parse_cors, _DEV_CORS


class TestCors(unittest.TestCase):
    def test_default_has_no_wildcard(self):
        parsed = _parse_cors(None)
        self.assertEqual(parsed, _DEV_CORS)
        self.assertNotIn("*", parsed)

    def test_parses_comma_separated_env(self):
        parsed = _parse_cors("https://a.example.com, https://b.example.com ")
        self.assertEqual(parsed, ["https://a.example.com", "https://b.example.com"])

    def test_empty_string_falls_back_to_dev(self):
        self.assertEqual(_parse_cors(""), _DEV_CORS)


class TestPostgresPortability(unittest.TestCase):
    def test_postgres_url_parses_to_postgres_dialect(self):
        # Verify the Postgres DSN resolves to the postgresql backend without
        # requiring the psycopg2 driver to be installed (it isn't, offline).
        from sqlalchemy.engine import make_url
        url = make_url("postgresql+psycopg2://u:p@localhost:5432/brandvault")
        self.assertEqual(url.get_backend_name(), "postgresql")
        self.assertEqual(url.database, "brandvault")

    def test_models_use_portable_types(self):
        # All mapped columns should be generic SQLAlchemy types (portable to PG).
        from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON
        import backend.app.models  # noqa: F401
        from backend.app.db.base import Base
        portable = (String, Text, Integer, Float, Boolean, DateTime, JSON)
        for table in Base.metadata.tables.values():
            for col in table.columns:
                self.assertIsInstance(
                    col.type, portable,
                    f"{table.name}.{col.name} uses non-portable type {col.type!r}",
                )


if __name__ == "__main__":
    unittest.main()
