# legacy/utils/type_mapping.py

def map_foxpro_type_to_sql(fox_type, size, decimals):
    t = fox_type.upper()

    if t == "C":  # character
        return "VARCHAR(" + str(size) + ")"

    if t == "N":  # numeric
        if decimals == 0:
            return "INT"
        return "DECIMAL(" + str(size) + "," + str(decimals) + ")"

    if t == "D":  # date
        return "DATE"

    if t == "L":  # logical
        return "BOOLEAN"

    if t == "M":  # memo
        return "TEXT"

    # fallback
    return "VARCHAR(255)"
