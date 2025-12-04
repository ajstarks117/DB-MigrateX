# app.py

from migrmgr.executor_mysql import MySQLMigrationExecutor
from normalizer.normalizer import NormalizationExecutor

def main():
    # 1. Migrate FoxPro -> staging DB (dbmigratex)
    print("=== STEP 1: FoxPro -> MySQL staging (dbmigratex) ===")
    mig = MySQLMigrationExecutor()
    mig.run_full_migration()

    # 2. Normalize staging data -> normalized DB (dbmigratex_norm)
    print("\n=== STEP 2: Normalization into dbmigratex_norm ===")
    norm = NormalizationExecutor()
    norm.run_full_normalization()

    print("\n✅ All done!")
    print("   Staging DB       :", mig.target_cfg['DATABASE_NAME'])
    print("   Normalized DB    :", norm.normalized_db)

if __name__ == "__main__":
    main()
