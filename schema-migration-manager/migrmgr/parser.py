"""Migration parser: parse SQL files, YAML metadata, and compute checksums.

Requires PyYAML (yaml.safe_load) for parsing YAML sidecars and inline
metadata. The parser preserves zero-padded numeric IDs by using the file
stem width when YAML provides an unquoted numeric id (e.g. `id: 001`).
"""
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
    meta_lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('--'):
            content = stripped[2:].lstrip()
            meta_lines.append(content)
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

    yml_path = sql_path.with_suffix('.yml')
    if not yml_path.exists():
        yml_path = sql_path.with_suffix('.yaml')

    file_meta = {}
    if yml_path.exists():
        try:
            file_meta = yaml.safe_load(yml_path.read_text(encoding='utf8')) or {}
            if not isinstance(file_meta, dict):
                raise MigrationParseError(f"Migration YAML must be a mapping: {yml_path}")
        except Exception as exc:
            raise MigrationParseError(f"Failed to parse YAML {yml_path}: {exc}")

    merged = {}
    merged.update(inline_meta or {})
    merged.update(file_meta or {})

    raw_id = merged.get('id')
    stem_prefix = sql_path.stem.split('_', 1)[0]
    if raw_id is None:
        base_id = stem_prefix
    else:
       
        if isinstance(raw_id, int):
            base_id = str(raw_id).zfill(len(stem_prefix))
        else:
            base_id = str(raw_id)

    filename = merged.get('filename') or sql_path.name
    author = merged.get('author')
    description = merged.get('description')
    requires = merged.get('requires') or []
    if requires is None:
        requires = []
    seen = set()
    deduped_requires = []
    for r in requires:
        if r not in seen:
            seen.add(r)
            deduped_requires.append(r)

    down_filename = merged.get('down_filename')
    # Auto-detect companion _down.sql file if not provided in metadata
    if not down_filename:
        down_path = sql_path.with_name(sql_path.stem + "_down.sql")
        if down_path.exists():
            down_filename = down_path.name
    mtype = merged.get('type')
    chksum = checksum(str(sql_path))

    return Migration(
        id=str(base_id),
        filename=filename,
        up_sql=_canonicalize_text(sql_text),
        down_filename=down_filename,
        author=author,
        description=description,
        requires=deduped_requires,
        checksum=chksum,
        type=mtype,
    )


def parse_migrations(dir_path: str) -> List[Migration]:
    p = pathlib.Path(dir_path)
    if not p.exists():
        return []
    migrations = []
    for sql in sorted(p.glob('*.sql')):
        if sql.name.endswith('_down.sql') or sql.name.endswith('.down.sql'):
            continue
        migrations.append(parse_migration(str(sql)))
    return migrations


__all__ = ['Migration', 'MigrationParseError', 'parse_migration', 'parse_migrations', 'checksum']
"""Migration parser: read SQL migration files, optional YAML metadata, and compute checksum.

This module provides a small YAML fallback loader when PyYAML isn't installed so
tests/examples in the repository work without extra dependencies.
"""
from dataclasses import dataclass
from typing import List, Optional
import hashlib
import pathlib

import yaml

def _safe_load(s: str):
    return yaml.safe_load(s)


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
    text = p.read_text(encoding="utf8")
    canon = _canonicalize_text(text)
    return hashlib.sha256(canon.encode("utf8")).hexdigest()


def _parse_inline_metadata(sql_text: str) -> dict:
    meta_lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            content = stripped[2:].lstrip()
            meta_lines.append(content)
            continue
        break

    if not meta_lines:
        return {}

    yaml_text = "\n".join(meta_lines)
    try:
        data = _safe_load(yaml_text)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def parse_migration(sql_path: str) -> Migration:
    sql_path = pathlib.Path(sql_path)
    if not sql_path.exists():
        raise MigrationParseError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf8")
    inline_meta = _parse_inline_metadata(sql_text)

    yml_path = sql_path.with_suffix('.yml')
    if not yml_path.exists():
        yml_path = sql_path.with_suffix('.yaml')

    file_meta = {}
    if yml_path.exists():
        try:
            file_meta = _safe_load(yml_path.read_text(encoding='utf8')) or {}
            if not isinstance(file_meta, dict):
                raise MigrationParseError(f"Migration YAML must be a mapping: {yml_path}")
        except Exception as exc:
            raise MigrationParseError(f"Failed to parse YAML {yml_path}: {exc}")

    merged = {}
    merged.update(inline_meta or {})
    merged.update(file_meta or {})

    raw_id = merged.get('id')
    stem_prefix = sql_path.stem.split('_', 1)[0]
    if raw_id is None:
        base_id = stem_prefix
    else:
        # preserve leading zeros if YAML parsed numeric values (e.g. 001 -> int 1)
        if isinstance(raw_id, int):
            base_id = str(raw_id).zfill(len(stem_prefix))
        else:
            base_id = str(raw_id)
    filename = merged.get('filename') or sql_path.name
    author = merged.get('author')
    description = merged.get('description')
    requires = merged.get('requires') or []
    if requires is None:
        requires = []
    seen = set()
    deduped_requires = []
    for r in requires:
        if r not in seen:
            seen.add(r)
            deduped_requires.append(r)

    down_filename = merged.get('down_filename')
    # Auto-detect companion _down.sql file when present
    if not down_filename:
        down_path = sql_path.with_name(sql_path.stem + "_down.sql")
        if down_path.exists():
            down_filename = down_path.name
    mtype = merged.get('type')

    chksum = checksum(str(sql_path))

    return Migration(
        id=str(base_id),
        filename=filename,
        up_sql=_canonicalize_text(sql_text),
        down_filename=down_filename,
        author=author,
        description=description,
        requires=deduped_requires,
        checksum=chksum,
        type=mtype,
    )


def parse_migrations(dir_path: str) -> List[Migration]:
    p = pathlib.Path(dir_path)
    if not p.exists():
        return []
    migrations = []
    for sql in sorted(p.glob('*.sql')):
        if sql.name.endswith('_down.sql') or sql.name.endswith('.down.sql'):
            continue
        migrations.append(parse_migration(str(sql)))
    return migrations


__all__ = [
    'Migration', 'MigrationParseError', 'parse_migration', 'parse_migrations', 'checksum'
]

"""Migration parser: read SQL migration files, optional YAML metadata, and compute checksum.

Responsibilities:
- For each SQL file, look for a sidecar YAML file with same base name (.yml or .yaml).
- Parse optional inline metadata from initial SQL comment lines (key: value pairs).
- Compute sha256 checksum of canonicalized SQL content.
- Return a Migration object with fields used by planner/executor.
"""
from dataclasses import dataclass
from typing import List, Optional
import hashlib
import pathlib

try:
    import yaml
    def _safe_load(s: str):
        return yaml.safe_load(s)
except Exception:
    def _safe_load(s: str):
        result = {}
        current_key = None
        for raw in s.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith('- '):
                val = line[2:].strip()
                if current_key:
                    result.setdefault(current_key, []).append(val)
                continue
            if ':' in line:
                k, v = line.split(':', 1)
                k = k.strip()
                v = v.strip().strip('"')
                if v == '':
                    result[k] = []
                    current_key = k
                else:
                    result[k] = v
                    current_key = k
                continue
        return result


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
    text = p.read_text(encoding="utf8")
    canon = _canonicalize_text(text)
    return hashlib.sha256(canon.encode("utf8")).hexdigest()


def _parse_inline_metadata(sql_text: str) -> dict:
    meta_lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            content = stripped[2:].lstrip()
            meta_lines.append(content)
            continue
        break

    if not meta_lines:
        return {}

    yaml_text = "\n".join(meta_lines)
    try:
        data = _safe_load(yaml_text)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def parse_migration(sql_path: str) -> Migration:
    sql_path = pathlib.Path(sql_path)
    if not sql_path.exists():
        raise MigrationParseError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf8")
    inline_meta = _parse_inline_metadata(sql_text)

    yml_path = sql_path.with_suffix('.yml')
    if not yml_path.exists():
        yml_path = sql_path.with_suffix('.yaml')

    file_meta = {}
    if yml_path.exists():
        try:
            file_meta = _safe_load(yml_path.read_text(encoding='utf8')) or {}
            if not isinstance(file_meta, dict):
                raise MigrationParseError(f"Migration YAML must be a mapping: {yml_path}")
        except Exception as exc:
            raise MigrationParseError(f"Failed to parse YAML {yml_path}: {exc}")

    merged = {}
    merged.update(inline_meta or {})
    merged.update(file_meta or {})

    raw_id = merged.get('id')
    stem_prefix = sql_path.stem.split('_', 1)[0]
    if raw_id is None:
        base_id = stem_prefix
    else:
        # preserve leading zeros if YAML parsed numeric values (e.g. 001 -> int 1)
        if isinstance(raw_id, int):
            base_id = str(raw_id).zfill(len(stem_prefix))
        else:
            base_id = str(raw_id)
    filename = merged.get('filename') or sql_path.name
    author = merged.get('author')
    description = merged.get('description')
    requires = merged.get('requires') or []
    if requires is None:
        requires = []
    seen = set()
    deduped_requires = []
    for r in requires:
        if r not in seen:
            seen.add(r)
            deduped_requires.append(r)

    down_filename = merged.get('down_filename')
    mtype = merged.get('type')

    chksum = checksum(str(sql_path))

    return Migration(
        id=str(base_id),
        filename=filename,
        up_sql=_canonicalize_text(sql_text),
        down_filename=down_filename,
        author=author,
        description=description,
        requires=deduped_requires,
        checksum=chksum,
        type=mtype,
    )


__all__ = [
    'Migration',
    'MigrationParseError',
    'parse_migration',
    'checksum',
]
import os
from typing import List, Tuple


class MigrationParser:
    def __init__(self, migrations_dir: str):
        self.migrations_dir = migrations_dir

    def get_migration_files(self) -> List[Tuple[str, str]]:
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith(".sql")]
        files.sort()
        migrations = []
        for file in files:
            with open(os.path.join(self.migrations_dir, file), 'r') as f:
                sql_content = f.read()
                migrations.append((file.split('.')[0], sql_content))
        return migrations


# Override/ensure a robust parse_migrations that auto-detects _down.sql companions
from pathlib import Path as _Path
def parse_migrations(dir_path: str) -> List[Migration]:
    p = _Path(dir_path)
    if not p.exists():
        return []
    migrations = []
    for sql in sorted(p.glob('*.sql')):
        if sql.name.endswith('_down.sql') or sql.name.endswith('.down.sql'):
            continue
        m = parse_migration(str(sql))
        if not getattr(m, 'down_filename', None):
            down = sql.with_name(sql.stem + "_down.sql")
            if down.exists():
                m.down_filename = down.name
        migrations.append(m)
    return migrations