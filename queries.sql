CREATE VIEW View_PL_Budget_Variance AS
WITH MonthlyActuals AS (
    SELECT 
        DATETRUNC(month, posting_date) AS reporting_month,
        department,
        expense_category,
        SUM(amount_usd) AS total_actual_spend
    FROM Fact_GL_Actuals
    GROUP BY DATETRUNC(month, posting_date), department, expense_category
),
MonthlyBudget AS (
    SELECT 
        budget_month AS reporting_month,
        department,
        SUM(budgeted_amount_usd) AS total_budgeted_spend
    FROM Fact_Department_Budget
    GROUP BY budget_month, department
)
SELECT 
    a.reporting_month,
    a.department,
    a.expense_category,
    b.total_budgeted_spend,
    a.total_actual_spend,
    (a.total_actual_spend - b.total_budgeted_spend) AS variance_usd,
    ROUND(((a.total_actual_spend - b.total_budgeted_spend) / NULLIF(b.total_budgeted_spend, 0)) * 100, 2) AS variance_pct,
    -- Audit Flag for Vendor Inflation Anomalies (>15% over budget)
    CASE 
        WHEN ((a.total_actual_spend - b.total_budgeted_spend) / NULLIF(b.total_budgeted_spend, 0)) >= 0.15 
             AND a.department != 'Engineering'
        THEN 'CRITICAL: Unexpected Software Inflation'
        WHEN a.total_actual_spend > b.total_budgeted_spend 
        THEN 'WARNING: Over Budget'
        ELSE 'WITHIN BUDGET'
    END AS audit_status
FROM MonthlyActuals a
LEFT JOIN MonthlyBudget b 
    ON a.reporting_month = b.reporting_month 
   AND a.department = b.department;
