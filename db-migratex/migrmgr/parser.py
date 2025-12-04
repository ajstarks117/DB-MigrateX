# migrmgr/parser.py
from dataclasses import dataclass
from typing import Optional, List
import pathlib
import hashlib


@dataclass
class Migration:
    id: str
    filename: str
    up_sql: str
    down_filename: Optional[str]
    checksum: str


def _canonicalize(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in t.split("\n")]
    return "\n".join(lines).strip()


def _checksum(path: str) -> str:
    p = pathlib.Path(path)
    txt = p.read_text(encoding="utf8")
    return hashlib.sha256(_canonicalize(txt).encode("utf8")).hexdigest()


def parse_migration(path: str) -> Migration:
    p = pathlib.Path(path)
    txt = p.read_text(encoding="utf8")

    # read inline metadata from comments like: -- id: 001, -- down_filename: ...
    meta = {}
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("--"):
            s = s[2:].strip()
            if ":" in s:
                k, v = s.split(":", 1)
                meta[k.strip()] = v.strip()
        else:
            break

    mig_id = meta.get("id") or p.stem.split("_", 1)[0]
    down = meta.get("down_filename")
    if not down:
        guess = p.with_suffix(".down.sql")
        if guess.exists():
            down = guess.name

    return Migration(
        id=str(mig_id),
        filename=p.name,
        up_sql=_canonicalize(txt),
        down_filename=down,
        checksum=_checksum(str(p)),
    )


def parse_migrations(dir_path: str) -> List[Migration]:
    p = pathlib.Path(dir_path)
    if not p.exists():
        return []
    out = []
    for f in sorted(p.glob("*.up.sql")):
        out.append(parse_migration(str(f)))
    return out
