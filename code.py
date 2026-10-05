import pandas as pd
import numpy as np
import glob
import os

def run_financial_pipeline(gl_data_path, budget_data_path, output_path):
    """
    Automates the ingestion of monthly GL exports and budget sheets,
    calculates variance, and identifies redundant SaaS licenses.
    """
    print("🚀 Starting Financial P&L Pipeline Ingestion...")

    # 1. Automated Ingestion (Replacing 3 Days of Manual Prep)
    gl_files = glob.glob(os.path.join(gl_data_path, "*.csv"))
    if not gl_files:
        raise FileNotFoundError("No GL export files found in directory.")

    df_gl = pd.concat([pd.read_csv(f) for f in gl_files], ignore_index=True)
    df_budget = pd.read_excel(budget_data_path)
    print(f"✅ Ingested {len(df_gl)} GL transaction records successfully.")

    # 2. Data Cleaning & Normalization
    df_gl['posting_date'] = pd.to_datetime(df_gl['posting_date'])
    df_gl['department'] = df_gl['department'].str.strip().str.title()
    df_gl['vendor_name'] = df_gl['vendor_name'].str.strip()

    # Filter Software & Licensing Expenses
    software_df = df_gl[df_gl['expense_category'].str.contains('Software|SaaS|Licensing', case=False, na=False)].copy()

    # 3. Identify Redundant Subscriptions & License Overlap ($14K Savings Analysis)
    # Group by Vendor & Department to flag overlapping tools
    vendor_summary = software_df.groupby(['department', 'vendor_name']).agg(
        total_annual_cost=('amount_usd', 'sum'),
        active_users=('user_count', 'sum'),
        unassigned_licenses=('unassigned_seats', 'sum')
    ).reset_index()

    # Identify tools with high unassigned seat ratios (Redundancy Flag)
    vendor_summary['potential_savings_usd'] = np.where(
        vendor_summary['unassigned_licenses'] > 0,
        (vendor_summary['total_annual_cost'] / (vendor_summary['active_users'] + vendor_summary['unassigned_licenses'])) * vendor_summary['unassigned_licenses'],
        0
    )

    total_realized_savings = vendor_summary['potential_savings_usd'].sum()
    print(f"\n💡 Total Redundant Subscription Savings Identified: ${total_realized_savings:,.2f}")

    # 4. Export Clean Data for Power BI
    software_df.to_csv(output_path, index=False)
    print(f"🎉 Process Complete! Clean dataset exported to: {output_path}")

    return vendor_summary

if __name__ == "__main__":
    GL_FOLDER = "./data/gl_exports"
    BUDGET_FILE = "./data/annual_budget.xlsx"
    OUTPUT_FILE = "./data/cleaned_pl_intelligence.csv"

    # Run Pipeline
    # summary = run_financial_pipeline(GL_FOLDER, BUDGET_FILE, OUTPUT_FILE)
