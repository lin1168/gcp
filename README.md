# GCP Cost Monitoring & Forecasting Toolkit

**Contributors:**
- Perry (Pei-An) Lin  
- Akylai (Aki) Batyrbekova  
- Kunhee (Lisa) Lee

A lightweight, end-to-end toolkit for analyzing and forecasting Google Cloud Platform (GCP) cost data. Includes three main components:

- **Forecasting:** Daily and monthly cost prediction using Prophet
- **Preprocessing:** Aggregate raw billing data and compute moving averages
- **Dashboard:** Interactive Streamlit app for anomaly detection and visualization

---

## Repository Structure

| File               | Description                                                 |
|--------------------|-------------------------------------------------------------|
| `prophet_pl.py`    | Forecasts total cost using Facebook Prophet (daily + monthly outputs) |
| `process_data.py`  | Aggregates raw CSVs, computes MAs, %/$ changes, saves Parquet output |
| `dashboard_app.py` | Streamlit dashboard for filtering and visualizing cost trends         |

---

## 1 Forecasting Script (`prophet_pl.py`)

### Requirements
```bash
pip install pandas matplotlib prophet
```

### Input CSV Format
| Column       | Description                 |
|--------------|-----------------------------|
| `usage_date` | Date in YYYY-MM-DD format   |
| `total_cost` | Daily total GCP cost        |

### Run the Script
```bash
python prophet_pl.py --input your_input.csv --daily_output daily_forecast.csv --monthly_output monthly_forecast.csv
```

### Output
- `daily_forecast.csv`: Daily forecast with uncertainty intervals
- `monthly_forecast.csv`: Aggregated monthly total cost forecast
- `forecast_plot.png`: Visualization of observed, fitted, and forecasted cost

---

## 2 Data Preprocessing (`process_data.py`)

### Requirements
```bash
pip install pandas tqdm pyarrow
# or
pip install fastparquet
```

### Functionality
- Filters CSVs in `data_dir` by date
- Aggregates daily cost per project
- Computes moving averages (7, 15, 30, 60, 90, 120)
- Calculates % and $ change vs. MA
- Saves output as `processed_data.parquet`

---

## 3 Streamlit Dashboard (`dashboard_app.py`)

### Requirements
```bash
pip install streamlit pandas matplotlib pyarrow
```

### Launch Dashboard
```bash
streamlit run dashboard_app.py
```

### Features
- Interactive filters: date, % change, $ change, increase/decrease
- Project-level visualization of total cost and moving average
- Real-time anomaly detection based on custom thresholds
