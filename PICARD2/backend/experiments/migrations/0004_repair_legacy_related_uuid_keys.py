import uuid

from django.db import migrations


def _to_text(value):
    if value is None:
        return ''
    if isinstance(value, bytes):
        value = value.decode()
    return str(value).strip()


def _try_uuid_hex(value):
    try:
        return uuid.UUID(_to_text(value)).hex
    except (AttributeError, TypeError, ValueError):
        return None


def _next_uuid_hex(used_ids):
    while True:
        candidate = uuid.uuid4().hex
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate


def _repair_primary_keys(cursor, table_name, dependent_columns):
    cursor.execute(f"SELECT id FROM {table_name}")
    rows = cursor.fetchall()

    used_ids = set()
    legacy_ids = []
    for (raw_id,) in rows:
        normalized_uuid = _try_uuid_hex(raw_id)
        if normalized_uuid:
            used_ids.add(normalized_uuid)
            continue
        legacy_ids.append(_to_text(raw_id))

    for legacy_id in legacy_ids:
        new_id = _next_uuid_hex(used_ids)
        cursor.execute(
            f"UPDATE {table_name} SET id = %s WHERE id = %s",
            [new_id, legacy_id],
        )
        for dependent_table, dependent_column in dependent_columns:
            cursor.execute(
                f"UPDATE {dependent_table} SET {dependent_column} = %s WHERE {dependent_column} = %s",
                [new_id, legacy_id],
            )


def repair_legacy_related_uuid_keys(apps, schema_editor):
    del apps
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        try:
            _repair_primary_keys(
                cursor,
                'datasets_csvdataset',
                [('experiments_sparkexperiment', 'dataset_id')],
            )
            _repair_primary_keys(
                cursor,
                'scripts_script',
                [('experiments_sparkexperiment', 'script_id')],
            )
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0002_alter_csvdataset_file_alter_csvdataset_id'),
        ('scripts', '0002_remove_script_content_script_file_alter_script_id'),
        ('experiments', '0003_sparkexperiment_args'),
    ]

    operations = [
        migrations.RunPython(repair_legacy_related_uuid_keys, migrations.RunPython.noop),
    ]