"""Peewee migrations -- extend memory records with routing-friendly metadata."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator

with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_fields(
        'memory',
        kind=pw.CharField(max_length=255, null=True, default='fact'),
        source=pw.CharField(max_length=255, null=True),
        enabled=pw.BooleanField(default=True),
    )

    migrator.sql("UPDATE memory SET kind = 'fact' WHERE kind IS NULL;")
    migrator.sql('UPDATE memory SET enabled = TRUE WHERE enabled IS NULL;')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_fields('memory', 'kind', 'source', 'enabled')
