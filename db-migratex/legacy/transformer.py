
def transform_student_record(raw: dict) -> dict:
    """
    Map BoxPro fields -> raw_students table schema.
    """
    return {
        "legacy_id": raw.get("ID"),
        "name": raw.get("NAME"),
        "age": int(raw.get("AGE", "0")),
        "department": raw.get("DEPT"),
    }
