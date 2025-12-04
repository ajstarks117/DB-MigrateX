from config import DB_CONFIG
from legacy.importer_foxpro import FoxProImporter

def main():
    importer = FoxProImporter(DB_CONFIG["SOURCE"]["DBF_ROOT"])
    tables = importer.list_tables()
    print("FoxPro tables found:", tables)

    for tname in tables:
        print("\n=== Table:", tname, "===")

        # Count rows using our reader
        total_rows = 0
        first_few = []

        for batch in importer.get_table_rows(tname, batch_size=5):
            total_rows += len(batch)
            # capture first 5 rows only
            for row in batch:
                if len(first_few) < 5:
                    first_few.append(row)

        print("Total rows seen by importer:", total_rows)
        if first_few:
            print("First few rows:")
            for r in first_few:
                print(" ", r)
        else:
            print("No rows returned by reader.")

if __name__ == "__main__":
    main()
