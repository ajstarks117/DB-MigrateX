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
    import yaml  # type: ignore
    def _safe_load(s: str):
        return yaml.safe_load(s)
except Exception:
    # minimal YAML fallback for very small, simple YAML used in migration metadata
    def _safe_load(s: str):
        # support simple mappings and lists with '- '
        result = {}
        current_key = None
        for raw in s.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith('- '):
                # list entry
                val = line[2:].strip()
                if current_key:
                    result.setdefault(current_key, []).append(val)
                continue
            if ':' in line:
                k, v = line.split(':', 1)
                k = k.strip()
                v = v.strip().strip('"')
                if v == '':
                    # start of a list or nested block
                    result[k] = []
                    current_key = k
                else:
                    result[k] = v
                    current_key = k
                continue
            # ignore unrecognized lines
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
    # normalize newlines and strip trailing spaces
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # strip trailing spaces per line
    lines = [l.rstrip() for l in text.split('\n')]
    return "\n".join(lines).strip()


def checksum(path: str) -> str:
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf8")
    canon = _canonicalize_text(text)
    return hashlib.sha256(canon.encode("utf8")).hexdigest()


def _parse_inline_metadata(sql_text: str) -> dict:
    """Parse initial SQL comment lines for key: value pairs.

    Recognizes leading comment lines that look like: -- key: value
    Stops on first non-comment line.
    Returns a dict (possibly empty).
    """
    meta_lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            content = stripped[2:].lstrip()
            # Only include lines that look like YAML key: value or start a YAML block
            meta_lines.append(content)
            continue
        # stop at first non-comment
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
        # if inline metadata is malformed, ignore it (parser can enforce strictness if desired)
        return {}


def parse_migration(sql_path: str) -> Migration:
    sql_path = pathlib.Path(sql_path)
    if not sql_path.exists():
        raise MigrationParseError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf8")
    inline_meta = _parse_inline_metadata(sql_text)

    # look for sidecar YAML
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

    # Merge metadata: YAML sidecar overrides inline
    merged = {}
    merged.update(inline_meta or {})
    merged.update(file_meta or {})

    # required fields
    base_id = merged.get('id') or sql_path.stem.split('_', 1)[0]
    filename = merged.get('filename') or sql_path.name
    author = merged.get('author')
    description = merged.get('description')
    requires = merged.get('requires') or []
    if requires is None:
        requires = []
    # dedupe requires preserving order
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
        """Get all .sql migration files sorted by version."""
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith(".sql")]
        files.sort()  # Sort by version (e.g., 001_create_users.sql)
        migrations = []
        for file in files:
            with open(os.path.join(self.migrations_dir, file), 'r') as f:
                sql_content = f.read()
                migrations.append((file.split('.')[0], sql_content))
        return migrations