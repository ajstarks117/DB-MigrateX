# app.py

import concurrent.futures
import time
from migrmgr.executor_mysql import MySQLMigrationExecutor
from normalizer.normalizer import NormalizationExecutor
from cleaner.cleanser import DataCleanser
from utils.forensics import recorder
from utils.reporter import generate_pdf_report
# [NEW] Import the analyzer
from analysis.nds_calculator import calculate_nds

def main():
    try:
        start_time = time.time()
        
        # --- PHASE 1: MIGRATION & ANALYSIS ---
        print("=== STEP 1: FoxPro -> Staging (Parallel Engine) ===")
        mig = MySQLMigrationExecutor()
        mig.setup_database_and_schema()
        
        tables = mig.list_tables()
        
        # [NEW] Pre-Migration NDS Analysis
        print("\n🧠 Running Normalization Dependency Analysis (AI Engine)...")
        for t in tables:
            # We fetch just one batch (up to 500 rows) to analyze the structure
            # This is fast and gives a good statistical approximation
            rows_gen = mig.importer.get_table_rows(t, batch_size=500)
            try:
                first_batch = next(rows_gen) # Get first chunk
                if first_batch:
                    score, notes = calculate_nds(t, first_batch)
                    
                    # Log the score to the dashboard
                    details = f"NDS Score: {score}/100. " + (" ".join(notes) if notes else "Structure looks good.")
                    severity = "High" if score > 50 else "Low"
                    
                    # We use 'recorder' to send this to the frontend
                    recorder.log_quality_issue(t, "NDS_SCORE", details)
                    print(f"   📊 {t}: NDS Score {score}/100")
            except StopIteration:
                print(f"   ⚠️ {t} is empty. Skipping analysis.")

        # Parallel Migration
        max_workers = 4
        print(f"\n🚀 Launching {max_workers} worker threads for {len(tables)} tables...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(mig.migrate_single_table, tables)
            
        print("✅ Parallel Migration Complete.")

        # --- PHASE 2: CLEANING (Smart Rules) ---
        print("\n=== STEP 2: Data Quality Scan ===")
        cleaner = DataCleanser()
        cleaner.run_diagnostics()
        recorder.save_report()

        # --- PHASE 3: NORMALIZATION ---
        print("\n=== STEP 3: Normalization ===")
        norm = NormalizationExecutor()
        norm.run_full_normalization()
        
        # --- PHASE 4: REPORTING ---
        print("\n=== STEP 4: Generating Audit Report ===")
        generate_pdf_report(output_path="Final_Audit_Report.pdf")

        duration = time.time() - start_time
        print(f"\n🎉 All done in {duration:.2f} seconds!")

    except Exception as e:
        recorder.log_error("MAIN_CRASH", str(e))
        recorder.save_report()
        print(f"❌ Fatal Error: {e}")

if __name__ == "__main__":
    main()