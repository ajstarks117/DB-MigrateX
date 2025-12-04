# app.py
from migrmgr.executor_mysql import MySQLMigrationExecutor
from normalizer.normalizer import NormalizationExecutor
from cleaner.cleanser import DataCleanser
from utils.forensics import recorder

def main():
    try:
        # 1. Migration
        print("=== STEP 1: FoxPro -> Staging ===")
        mig = MySQLMigrationExecutor()
        mig.run_full_migration()

        # 2. Data Cleaning / Analysis
        print("\n=== STEP 2: Data Quality Scan ===")
        cleaner = DataCleanser()
        cleaner.run_full_scan()

        # 3. Normalization
        print("\n=== STEP 3: Normalization ===")
        norm = NormalizationExecutor()
        norm.run_full_normalization()

        print("\n✅ All done!")
    
    except Exception as e:
        recorder.log_error("MAIN_LOOP", str(e))
        print("❌ Fatal Error:", e)
    
    finally:
        # Always save the report at the end
        recorder.save_report()

if __name__ == "__main__":
    main()
