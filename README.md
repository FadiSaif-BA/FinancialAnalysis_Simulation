# 📊 Financial Data & Predictive Analytics

### *Simulation: Optimizing the Cash Conversion Cycle*

## 🎯 Project Overview

In large-scale infrastructure firms like **Parsons**, managing liquidity is a high-stakes challenge involving thousands of concurrent projects and global clients. This project automates the extraction, cleaning, and analysis of **10,000+ financial records** to solve the problem of "Hidden Liquidity Risk."

By transitioning from manual, static reporting to a **Python-driven automated engine**, this suite provides real-time visibility into cash flow velocity, revenue leakage, and payment volatility.

---

## 🛠️ The Tech Stack

* **Database:** Microsoft SQL Server (Developer Edition)
* **Language:** Python 3.14 (PyCharm IDE)
* **Key Libraries:** * `pyodbc`: For high-performance SQL-to-Python ETL.
* `pandas`: For advanced data manipulation and vectorization.
* `matplotlib/seaborn`: For financial trend visualization.


* **Architecture:** Relational Star Schema (Dimension & Fact Tables).

---

## 🧠 Business Problems & Technical Solutions

### 1. The Liquidity Problem: DSO & Aging

**Problem:** Inability to track the average time to collect cash leads to poor budgeting and high borrowing costs.

* **Task:** Automate **Days Sales Outstanding (DSO)** calculations and **Aging Buckets**.
* **The Math:** * DSO=(Average Accounts Receivable / Total Credit Sales)×Days in Period

    Logic: Multi-tier segmentation (0-30, 31-60, 61-90, 90+ days) to identify "Toxic Debt."
* **Logic:** Multi-tier segmentation (0-30, 31-60, 61-90, 90+ days) to identify "Toxic Debt."



### 2. The Operational Leakage Problem: WIP Analysis

**Problem:** Technical teams often prioritize engineering work over administrative billing, causing **Work in Progress (WIP)** to sit unbilled for months.

* **Task:** Detect "Stale WIP" and calculate the **Leakage Coefficient**.
* **The Math:** * Lc=∑Unbilled Value / ∑(Unbilled Value+Invoiced Value)
* **Goal:** Flag projects where work is being performed but not converted into cash.

### 3. The Predictive Risk Problem: Time-Series & Variance

**Problem:** Historical data alone is reactive. We need to predict which clients will violate their contracts next month.

* **Task:** **Cohort Analysis** and **Payment Variance** tracking.
* **The Math:** Variance=Actual Days to Pay − Contractual Terms

* **Goal:** Use **Moving Averages** to forecast quarterly cash inflow with a 95% confidence interval.

---

## 🏗️ Database Schema & Data Integrity

The system operates on a robust relational structure to ensure **Referential Integrity**:

* **`Clients` Table:** (n=100) Stores contractual terms and credit limits.
* **`Projects` Table:** (n=300) Segmented by Sector (Transport, Energy, etc.) and Region (Riyadh, NEOM).
* **`Invoices` Table:** (n=10,000) The core fact table tracking billing and collections.
* **`UnbilledWork` Table:** Tracks technical hours logged but not yet invoiced.

---

## 🚀 How to Run (One-Click Extraction)

The project is designed for "One-Click" execution via PyCharm:

1. **Configure Connection:** Update the `SERVER_NAME` in `config.py` to match your SQL Instance.
2. **Execute:** Run `main.py`.
3. **Output:** * The console will print a **Financial Health Check**.
* A timestamped **AR Snapshot** is saved to the `/reports/` folder.
* Predictive plots are generated for **DSO Trends**.

---

## 📈 Key Insights Generated

* **Top 10 Risk Projects:** A prioritized list for Project Directors to address immediately.
* **Client Grade Report:** Rankings (A-F) based on historical payment reliability.
* **Burn Rate vs. Billing:** Visualization of engineering output versus actual revenue recognized.

---

**Developed by:** Fadi A. Saif
**Focus:** Financial Data Engineering & Strategic Automation
