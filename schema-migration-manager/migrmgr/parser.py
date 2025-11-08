from dataclasses import dataclass
from typing import List, Optional
import hashlib
import pathlib
import yaml

class MigrationParseError(Exception):
    pass

@dataclass
class Migration:
    id: str
    filename: str
    up_sql: str
    down_filename: Optional[str]
    author: Optional[str]
    description: Optional[str]
    requires: List[str]
    checksum: str
    type: Optional[str]


def _canonicalize_text(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.rstrip() for l in text.split('\n')]
    return "\n".join(lines).strip()


def checksum(path: str) -> str:
    p = pathlib.Path(path)
    text = p.read_text(encoding='utf8')
    canon = _canonicalize_text(text)
    return hashlib.sha256(canon.encode('utf8')).hexdigest()


def _parse_inline_metadata(sql_text: str) -> dict:
    """Parses YAML metadata from comment lines at the top of the SQL file."""
    meta_lines = []
    for line in sql_text.splitlines():
        s = line.lstrip()
        if s.startswith("--"):
            meta_lines.append(s[2:].lstrip())
            continue
        break

    if not meta_lines:
        return {}

    yaml_text = "\n".join(meta_lines)
    try:
        data = yaml.safe_load(yaml_text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def parse_migration(sql_path: str) -> Migration:
    sql_path = pathlib.Path(sql_path)

    if not sql_path.exists():
        raise MigrationParseError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding='utf8')

    inline_meta = _parse_inline_metadata(sql_text) or {}

    # Look for sidecar YAML (.yml or .yaml)
    yml_path = sql_path.with_suffix(".yml")
    if not yml_path.exists():
        yml_path = sql_path.with_suffix(".yaml")

    file_meta = {}
    if yml_path.exists():
        try:
            file_meta = yaml.safe_load(yml_path.read_text()) or {}
        except Exception as e:
            # convert YAML parse errors into MigrationParseError for callers/tests
            raise MigrationParseError(f"Invalid migration YAML {yml_path}: {e}")

        if not isinstance(file_meta, dict):
            raise MigrationParseError(f"Migration YAML must be mapping: {yml_path}")

    # Merge inline YAML + .yml file
    merged = {**inline_meta, **file_meta}

    # Determine migration ID
    raw_id = merged.get("id")
    prefix = sql_path.stem.split("_", 1)[0]

    if raw_id is None:
        mig_id = prefix
    else:
        if isinstance(raw_id, int):
            mig_id = str(raw_id).zfill(len(prefix))
        else:
            mig_id = str(raw_id)

    # Dependencies
    requires = merged.get("requires") or []
    if not isinstance(requires, list):
        requires = []
    requires = list(dict.fromkeys(requires))  # remove duplicates

    # ✅ AUTO-DETECT DOWN FILE
    down = merged.get("down_filename")

    if not down:
        # e.g. 001_create_users.sql → 001_create_users_down.sql
        guess = sql_path.with_name(sql_path.stem + "_down.sql")
        if guess.exists():
            down = guess.name
        else:
            # fallback: use id_down.sql (e.g., 001_down.sql)
            guess2 = sql_path.with_name(f"{mig_id}_down.sql")
            if guess2.exists():
                down = guess2.name

    return Migration(
        id=mig_id,
        filename=sql_path.name,
        up_sql=_canonicalize_text(sql_text),
        down_filename=down,
        author=merged.get("author"),
        description=merged.get("description"),
        requires=requires,
        checksum=checksum(str(sql_path)),
        type=merged.get("type"),
    )


def parse_migrations(dir_path: str) -> List[Migration]:
    p = pathlib.Path(dir_path)
    if not p.exists():
        return []

    migrations = []
    for sql in sorted(p.glob("*.sql")):
        if sql.name.endswith("_down.sql"):
            continue
        migrations.append(parse_migration(str(sql)))

    return migrations
