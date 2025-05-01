import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load processed data
df = pd.read_parquet("processed_data.parquet")

# Ensure date column is fully visible
df['usage_date'] = pd.to_datetime(df['usage_date'])

# Title
st.title("Dexcom Google Cloud Cost Monitoring Dashboard")
st.markdown("Monitor cost trends and anomalies across Dexcom's cloud infrastructure.")

# Sidebar - Settings
st.sidebar.header("Settings")

# Show available date range
min_date, max_date = df['usage_date'].min(), df['usage_date'].max()
st.sidebar.markdown(f"**Available Date Range:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

# Select Moving Average period
ma_period = st.sidebar.selectbox("Select Moving Average Period:", [120, 90, 60, 30, 15, 7])

# Ensure selected date is within valid range
valid_start_date = min_date + pd.Timedelta(days=ma_period)

# Select Date (only allow dates where MA is valid)
available_dates = df[df['usage_date'] >= valid_start_date]['usage_date'].dt.strftime('%Y-%m-%d').unique()
date_selected = st.sidebar.selectbox("Select Date:", sorted(available_dates, reverse=True), index=0)
date_selected = pd.to_datetime(date_selected)

# Sidebar - Filtering
st.sidebar.header("Filters")

# Filter by increase or decrease change
change_type = st.sidebar.radio("Change Type:", ["Increase", "Decrease", "Both"], index=2)

# Define change amount filter
change_amount = st.sidebar.number_input("Minimum % Change (absolute value):", min_value=0, value=0, step=1)

# Filter projects by selected date and change criteria
df_filtered = df[df['usage_date'] == date_selected]
if change_type == "Increase":
    df_filtered = df_filtered[df_filtered[f'Change_%_{ma_period}'] >= change_amount]
elif change_type == "Decrease":
    df_filtered = df_filtered[df_filtered[f'Change_%_{ma_period}'] <= -change_amount]
else:
    df_filtered = df_filtered[(df_filtered[f'Change_%_{ma_period}'] >= change_amount) | (df_filtered[f'Change_%_{ma_period}'] <= -change_amount)]

# Filter by $ change range
min_dollar_change, max_dollar_change = df_filtered[f'Change_$_{ma_period}'].min(), df_filtered[f'Change_$_{ma_period}'].max()

# Ensure valid default values
if pd.isna(min_dollar_change) or pd.isna(max_dollar_change):
    min_dollar_change, max_dollar_change = 0, 0

# Syncing logic
def sync_dollar_values():
    global min_value_input, max_value_input, dollar_range
    min_value_input = st.session_state.min_dollar_input
    max_value_input = st.session_state.max_dollar_input
    dollar_range = (min_value_input, max_value_input)

def sync_dollar_slider():
    global min_value_input, max_value_input
    if st.session_state.dollar_slider != (min_value_input, max_value_input):
        min_value_input, max_value_input = st.session_state.dollar_slider
        st.session_state.min_dollar_input = min_value_input
        st.session_state.max_dollar_input = max_value_input

min_value_input = st.sidebar.number_input("Min $ Change:", value=min_dollar_change, step=1.0, key="min_dollar_input", on_change=sync_dollar_values)
max_value_input = st.sidebar.number_input("Max $ Change:", value=max_dollar_change, step=1.0, key="max_dollar_input", on_change=sync_dollar_values)
dollar_range = st.sidebar.slider(
    "$ Change Range:",
    min_value=min_dollar_change,
    max_value=max_dollar_change,
    value=(min_value_input, max_value_input),
    key="dollar_slider",
    on_change=sync_dollar_slider
)

df_filtered = df_filtered[(df_filtered[f'Change_$_{ma_period}'] >= dollar_range[0]) & (df_filtered[f'Change_$_{ma_period}'] <= dollar_range[1])]

# Allow user to select specific projects
selected_projects = st.sidebar.multiselect("Select Projects to Display:", df_filtered['project_id'].unique(), default=df_filtered['project_id'].unique())

df_filtered = df_filtered[df_filtered['project_id'].isin(selected_projects)]

# Display filtered data
st.data_editor(df_filtered[['project_id', f'MA_{ma_period}', 'total_cost', f'Change_%_{ma_period}', f'Change_$_{ma_period}']].rename(columns={
    'total_cost': "Today's Price",
    f'MA_{ma_period}': f"MA({ma_period})",
    f'Change_%_{ma_period}': "% Change",
    f'Change_$_{ma_period}': "$ Change"
}))

# Graph Settings
st.markdown("### Graph Settings")
col1, col2 = st.columns(2)
with col1:
    num_days_display = st.slider("Select Number of Days to Display:", min_value=7, max_value=365, value=120, step=5, key="num_days_display")
with col2:
    display_ma = st.checkbox("Display Moving Average", value=True, key="display_ma")

# Plotting section
st.markdown(f"### Cost Trend Over Last {num_days_display} Days (Ending {date_selected.strftime('%Y-%m-%d')})")
fig, ax = plt.subplots(figsize=(12, 6))

for project_id in selected_projects:
    project_data = df[df['project_id'] == project_id].sort_values('usage_date').set_index('usage_date')
    project_data = project_data[['total_cost', f'MA_{ma_period}']].resample('D').ffill()
    
    valid_project_start = min_date + pd.Timedelta(days=ma_period)
    project_data = project_data.loc[valid_project_start:date_selected].tail(num_days_display)

    # Plot cost line and capture its color
    cost_line, = ax.plot(
        project_data.index,
        project_data['total_cost'],
        marker='o',
        linestyle='-',
        linewidth=1,
        label=f"{project_id} - Cost"
    )
    line_color = cost_line.get_color()

    # Plot MA line with same color (if enabled)
    if display_ma:
        ax.plot(
            project_data.index,
            project_data[f'MA_{ma_period}'],
            linestyle='dashed',
            linewidth=1.5,
            alpha=0.7,
            color=line_color,
            label=f"{project_id} - MA({ma_period})"
        )

# Formatting
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45, ha='right', fontsize=10)

ax.set_xlabel("Usage Date")
ax.set_ylabel("Total Cost")
ax.set_title(f"Dexcom Cost Trend Over Last {num_days_display} Days (Ending {date_selected.strftime('%Y-%m-%d')})")
ax.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1, frameon=False)

# Render the figure
st.pyplot(fig)
