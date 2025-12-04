# legacy/parser_boxpro.py

def parse_boxpro_file(path: str):
    """
    Parses BoxPro .bxp file into a list of dicts.
    Format:

    ID: 101
    NAME: ...
    AGE: ...
    ---
    ID: 102
    ...

    """
    records = []
    current = {}

    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line == "---":
                if current:
                    records.append(current)
                    current = {}
                continue

            if ":" in line:
                k, v = line.split(":", 1)
                current[k.strip()] = v.strip()

    if current:
        records.append(current)

    return records
