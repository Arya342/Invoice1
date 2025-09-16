import pandas as pd
import numpy as np
from datetime import datetime

def analyze_data_quality():
    """Comprehensive data quality analysis for both datasets"""
    
    print("=" * 80)
    print("DATA QUALITY ANALYSIS REPORT")
    print("=" * 80)
    
    # Load datasets
    try:
        invoices_df = pd.read_csv('funding_invoices.csv')
        credit_notes_df = pd.read_csv('funding_invoice_credit_notes.csv')
        print("SUCCESS: Successfully loaded both datasets")
    except Exception as e:
        print(f"ERROR: Error loading data: {e}")
        return
    
    print(f"\nDATASET OVERVIEW")
    print(f"Funding Invoices: {len(invoices_df):,} rows × {len(invoices_df.columns)} columns")
    print(f"Credit Notes: {len(credit_notes_df):,} rows × {len(credit_notes_df.columns)} columns")
    
    # Analyze funding_invoices.csv 
    print("\n" + "="*50)
    print("FUNDING INVOICES ANALYSIS")
    print("="*50)
    
    analyze_dataset(invoices_df, "Funding Invoices")
    
    # Analyze funding_invoice_credit_notes.csv
    print("\n" + "="*50)
    print("CREDIT NOTES ANALYSIS")
    print("="*50)
    
    analyze_dataset(credit_notes_df, "Credit Notes")
    
    # Cross-dataset relationship analysis
    print("\n" + "="*50)
    print("RELATIONSHIP ANALYSIS")
    print("="*50)
    
    analyze_relationships(invoices_df, credit_notes_df)
    
    # Overall data quality summary
    print("\n" + "="*50)
    print("OVERALL DATA QUALITY SUMMARY")
    print("="*50)
    
    provide_quality_summary(invoices_df, credit_notes_df)

def analyze_dataset(df, dataset_name):
    """Analyze individual dataset quality"""
    
    print(f"\n{dataset_name.upper()} DETAILED ANALYSIS")
    
    # Basic info
    print(f"\nShape: {df.shape}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Missing values analysis
    print(f"\nMISSING VALUES:")
    missing_counts = df.isnull().sum()
    missing_percentages = (missing_counts / len(df)) * 100
    
    missing_summary = pd.DataFrame({
        'Column': missing_counts.index,
        'Missing_Count': missing_counts.values,
        'Missing_Percentage': missing_percentages.values
    }).sort_values('Missing_Percentage', ascending=False)
    
    # Show columns with missing values
    columns_with_missing = missing_summary[missing_summary['Missing_Count'] > 0]
    if len(columns_with_missing) > 0:
        print("Columns with missing values:")
        for _, row in columns_with_missing.head(10).iterrows():
            print(f"   {row['Column']}: {row['Missing_Count']:,} ({row['Missing_Percentage']:.1f}%)")
        if len(columns_with_missing) > 10:
            print(f"   ... and {len(columns_with_missing) - 10} more columns")
    else:
        print("No missing values found!")
    
    # Data types analysis
    print(f"\nDATA TYPES:")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"   {dtype}: {count} columns")
    
    # Identify potential issues
    print(f"\nPOTENTIAL DATA QUALITY ISSUES:")
    
    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        print(f"   Duplicate rows: {duplicates:,}")
    else:
        print(f"   No duplicate rows")
    
    # Check for columns that should be numeric but aren't
    numeric_candidates = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['amount', 'total', 'fee', 'gst', 'hours', 'units', 'payment']):
            if df[col].dtype == 'object':
                numeric_candidates.append(col)
    
    if numeric_candidates:
        print(f"   Columns that might need numeric conversion: {', '.join(numeric_candidates[:5])}")
        if len(numeric_candidates) > 5:
            print(f"      ... and {len(numeric_candidates) - 5} more")
    
    # Check for date columns
    date_candidates = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'created', 'modified']):
            if df[col].dtype == 'object':
                date_candidates.append(col)
    
    if date_candidates:
        print(f"   Columns that might need date conversion: {', '.join(date_candidates[:5])}")
    
    # Check for inconsistent categorical values
    categorical_issues = []
    for col in df.select_dtypes(include=['object']).columns:
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 20:  # Likely categorical
            values = df[col].value_counts()
            # Check for potential inconsistencies (case, spacing, etc.)
            unique_values = [str(v).strip().lower() for v in values.index if pd.notna(v)]
            if len(set(unique_values)) < len(unique_values):
                categorical_issues.append(col)
    
    if categorical_issues:
        print(f"   Categorical columns with potential inconsistencies: {', '.join(categorical_issues[:3])}")
    
    # Sample problematic data
    print(f"\nSAMPLE DATA (first 3 rows):")
    print(df.head(3).to_string())

def analyze_relationships(invoices_df, credit_notes_df):
    """Analyze relationships between datasets"""
    
    print(f"\nCROSS-DATASET RELATIONSHIPS:")
    
    # Check foreign key relationships
    if 'id' in invoices_df.columns and 'funding_invoice_id' in credit_notes_df.columns:
        invoice_ids = set(invoices_df['id'].dropna())
        credit_invoice_ids = set(credit_notes_df['funding_invoice_id'].dropna())
        
        # Orphaned credit notes
        orphaned_credits = credit_invoice_ids - invoice_ids
        if orphaned_credits:
            print(f"   Orphaned credit notes (no matching invoice): {len(orphaned_credits)}")
        else:
            print(f"   All credit notes have matching invoices")
        
        # Invoices with credit notes
        invoices_with_credits = invoice_ids & credit_invoice_ids
        print(f"   Invoices with credit notes: {len(invoices_with_credits):,} ({len(invoices_with_credits)/len(invoice_ids)*100:.1f}%)")
    
    # Check user_id consistency
    if 'user_id' in invoices_df.columns and 'user_id' in credit_notes_df.columns:
        invoice_users = set(invoices_df['user_id'].dropna())
        credit_users = set(credit_notes_df['user_id'].dropna())
        
        common_users = invoice_users & credit_users
        print(f"   Users appearing in both datasets: {len(common_users):,}")
        
        # Users only in credit notes
        credit_only_users = credit_users - invoice_users
        if credit_only_users:
            print(f"   Users in credit notes but not in invoices: {len(credit_only_users)}")

def provide_quality_summary(invoices_df, credit_notes_df):
    """Provide overall data quality assessment"""
    
    # Calculate quality scores
    invoice_quality_score = calculate_quality_score(invoices_df)
    credit_quality_score = calculate_quality_score(credit_notes_df)
    
    print(f"\nDATA QUALITY SCORES:")
    print(f"   Funding Invoices: {invoice_quality_score:.1f}/10")
    print(f"   Credit Notes: {credit_quality_score:.1f}/10")
    print(f"   Overall Average: {(invoice_quality_score + credit_quality_score)/2:.1f}/10")
    
    # Provide recommendations
    print(f"\nRECOMMENDATIONS:")
    
    if invoice_quality_score < 7 or credit_quality_score < 7:
        print("   DATA CLEANING NEEDED:")
        
        # Check for missing values
        invoice_missing = (invoices_df.isnull().sum().sum() / (len(invoices_df) * len(invoices_df.columns))) * 100
        credit_missing = (credit_notes_df.isnull().sum().sum() / (len(credit_notes_df) * len(credit_notes_df.columns))) * 100
        
        if invoice_missing > 5:
            print(f"   - Handle missing values in invoices ({invoice_missing:.1f}% missing)")
        if credit_missing > 5:
            print(f"   - Handle missing values in credit notes ({credit_missing:.1f}% missing)")
        
        print("   - Convert data types (dates, numbers)")
        print("   - Standardize categorical values")
        print("   - Validate foreign key relationships")
    else:
        print("   Data is relatively clean and ready for analysis")
        print("   - Minor cleaning may be beneficial")
        print("   - Consider data validation rules for future data")
    
    # Overall assessment
    avg_score = (invoice_quality_score + credit_quality_score) / 2
    if avg_score >= 8:
        quality_level = "EXCELLENT"
    elif avg_score >= 6:
        quality_level = "GOOD"
    elif avg_score >= 4:
        quality_level = "FAIR"
    else:
        quality_level = "POOR"
    
    print(f"\nOVERALL DATA QUALITY: {quality_level}")

def calculate_quality_score(df):
    """Calculate a quality score from 0-10 for a dataset"""
    score = 10.0
    
    # Penalize for missing values
    missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    score -= min(missing_percentage / 10, 3)  # Max 3 points deduction
    
    # Penalize for duplicates
    duplicate_percentage = (df.duplicated().sum() / len(df)) * 100
    score -= min(duplicate_percentage / 5, 2)  # Max 2 points deduction
    
    # Penalize for inconsistent data types
    object_columns = len(df.select_dtypes(include=['object']).columns)
    if object_columns / len(df.columns) > 0.7:  # Too many object columns
        score -= 1
    
    return max(score, 0)

if __name__ == "__main__":
    analyze_data_quality()  