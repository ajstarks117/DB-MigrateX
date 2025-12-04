# legacy/utils/dbf_reader.py

import struct

class DBFReader:
    """
    Simple DBF/FoxPro reader using only Python stdlib.
    Handles basic field types: C, N, D, L, M.
    """

    def _read_header(self, f):
        header = f.read(32)
        if len(header) < 32:
            raise ValueError("File too small to be a DBF")

        version = header[0]
        record_count = struct.unpack("<I", header[4:8])[0]
        header_length = struct.unpack("<H", header[8:10])[0]
        record_length = struct.unpack("<H", header[10:12])[0]

        # Read field descriptors (32 bytes each) until 0x0D
        fields = []
        while True:
            desc = f.read(32)
            if not desc:
                break
            if desc[0] == 0x0D:  # header terminator
                break

            # Field name: bytes 0–10, null-terminated
            raw_name = desc[0:11]
            zero_pos = 0
            while zero_pos < len(raw_name) and raw_name[zero_pos] != 0:
                zero_pos += 1
            name = raw_name[:zero_pos].decode("ascii", errors="ignore").strip()

            ftype_char = chr(desc[11])
            length = desc[16]
            decimals = desc[17]

            if name != "":
                field_info = {
                    "name": name,
                    "type": ftype_char,
                    "length": length,
                    "decimals": decimals,
                }
                fields.append(field_info)

        # Move to start of data
        f.seek(header_length)

        result = {
            "version": version,
            "record_count": record_count,
            "header_length": header_length,
            "record_length": record_length,
            "fields": fields,
        }
        return result

    def read_schema(self, dbf_path):
        """
        Returns list of:
        { "name": ..., "foxpro_type": ..., "size": ..., "decimals": ... }
        """
        f = open(dbf_path, "rb")
        try:
            header = self._read_header(f)
            cols = []
            i = 0
            while i < len(header["fields"]):
                fld = header["fields"][i]
                cols.append({
                    "name": fld["name"],
                    "foxpro_type": fld["type"],
                    "size": fld["length"],
                    "decimals": fld["decimals"],
                })
                i += 1
            return cols
        finally:
            f.close()

    def _strip_ascii(self, b):
        # basic replacement for strip/decode combos
        s = ""
        i = 0
        length = len(b)
        while i < length:
            ch = chr(b[i])
            # simple ASCII range check
            if 32 <= ord(ch) <= 126:
                s = s + ch
            elif ch == "\x00":
                # skip
                pass
            else:
                # ignore non-printable
                pass
            i += 1
        # trim spaces manually
        start = 0
        end = len(s)
        while start < end and s[start] == " ":
            start += 1
        while end > start and s[end - 1] == " ":
            end -= 1
        return s[start:end]

    def _parse_field_value(self, raw_bytes, field_type, decimals):
        text = self._strip_ascii(raw_bytes)
        if text == "":
            return None

        t = field_type.upper()

        if t == "C":  # Character
            return text

        if t == "N":  # Numeric
            # manually parse number
            has_dot = False
            j = 0
            while j < len(text):
                ch = text[j]
                if ch == ".":
                    has_dot = True
                    break
                j += 1

            # remove spaces
            tmp = ""
            k = 0
            while k < len(text):
                ch = text[k]
                if ch != " ":
                    tmp = tmp + ch
                k += 1
            text = tmp

            if text == "":
                return None

            # decide int or float
            if decimals == 0 and not has_dot:
                # parse as int
                neg = False
                idx = 0
                if text[0] == "-":
                    neg = True
                    idx = 1
                val = 0
                while idx < len(text):
                    ch = text[idx]
                    if ch >= "0" and ch <= "9":
                        digit = ord(ch) - ord("0")
                        val = val * 10 + digit
                    idx += 1
                if neg:
                    val = -val
                return val
            else:
                # parse float manually (simple)
                neg = False
                idx = 0
                if text[0] == "-":
                    neg = True
                    idx = 1

                integer_part = 0
                frac_part = 0
                frac_divisor = 1
                seen_dot = False

                while idx < len(text):
                    ch = text[idx]
                    if ch == ".":
                        seen_dot = True
                    else:
                        if ch >= "0" and ch <= "9":
                            digit = ord(ch) - ord("0")
                            if not seen_dot:
                                integer_part = integer_part * 10 + digit
                            else:
                                frac_part = frac_part * 10 + digit
                                frac_divisor = frac_divisor * 10
                    idx += 1

                value = integer_part + (frac_part / float(frac_divisor))
                if neg:
                    value = -value
                return value

        if t == "D":  # Date YYYYMMDD
            if len(text) == 8:
                year = text[0:4]
                month = text[4:6]
                day = text[6:8]
                return year + "-" + month + "-" + day
            return text

        if t == "L":  # Logical
            ch = text.upper()
            if ch == "Y" or ch == "T" or ch == "1":
                return True
            if ch == "N" or ch == "F" or ch == "0":
                return False
            return None

        if t == "M":  # Memo pointer (we treat as text key only)
            return text

        # default: raw text
        return text

    def read_rows(self, dbf_path, batch_size):
        """
        Yields list of dict rows in batches.
        """
        f = open(dbf_path, "rb")
        try:
            header = self._read_header(f)
            fields = header["fields"]
            rec_len = header["record_length"]

            rows_batch = []
            while True:
                record = f.read(rec_len)
                if not record or len(record) < rec_len:
                    break

                # first byte is deletion flag
                deleted_flag = record[0:1]
                if deleted_flag == b"*":
                    # deleted record, skip
                    continue

                offset = 1
                row = {}
                idx = 0
                while idx < len(fields):
                    fld = fields[idx]
                    length = fld["length"]
                    raw = record[offset:offset + length]
                    offset = offset + length

                    value = self._parse_field_value(raw, fld["type"], fld["decimals"])
                    row[fld["name"]] = value
                    idx += 1

                rows_batch.append(row)

                if len(rows_batch) >= batch_size:
                    yield rows_batch
                    rows_batch = []

            if len(rows_batch) > 0:
                yield rows_batch

        finally:
            f.close()
