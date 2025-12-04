# analysis/nds_calculator.py
import pandas as pd

def calculate_nds(table_name, data_list):
    """
    Analyzes a list of dictionaries (rows) and returns:
    1. A Score (0-100) where 100 means 'Bad / Needs Normalization'.
    2. A list of specific recommendations.
    """
    if not data_list:
        return 0, ["Table is empty."]

    # Convert list of dicts to a DataFrame for easy analysis
    df = pd.DataFrame(data_list)
    score = 0
    issues = []
    
    row_count = len(df)
    col_count = len(df.columns)

    # --- FACTOR 1: Column Redundancy (50 points max) ---
    # Logic: If a column (like City) has 1000 rows but only 5 unique values, 
    # it is highly redundant (Redundancy Ratio < 10%).
    redundant_cols = []
    for col in df.columns:
        # Check text columns only
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            unique_count = df[col].nunique()
            ratio = unique_count / row_count if row_count > 0 else 0
            
            # If unique values are < 10% of total rows, it's a candidate for extraction
            if ratio < 0.1 and unique_count > 1: 
                redundant_cols.append(col)
                score += 10 # Add penalty points

    if redundant_cols:
        issues.append(f"High Redundancy in: {', '.join(redundant_cols)}. Suggest extracting to master tables.")

    # --- FACTOR 2: Null Density (30 points max) ---
    # Logic: If a table is > 30% empty, it might be violating 1NF (Sparse Matrix).
    total_cells = row_count * col_count
    null_cells = df.isnull().sum().sum()
    null_ratio = null_cells / total_cells if total_cells > 0 else 0
    
    if null_ratio > 0.3:
        score += 30
        issues.append(f"Sparse Data ({int(null_ratio*100)}% Empty). Potential 1NF violation.")

    # --- FACTOR 3: Table Width (20 points max) ---
    # Logic: Tables with too many columns often need vertical splitting.
    if col_count > 15:
        score += 20
        issues.append(f"Table is too wide ({col_count} columns). Consider vertical partitioning.")

    # Cap score at 100 (0 = Perfect 3NF, 100 = Flat File Mess)
    final_score = min(score, 100)
    
    return final_score, issues