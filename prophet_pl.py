import argparse
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet


def train_and_forecast(input_csv, daily_output_csv, monthly_output_csv):
    # Load the input data
    df = pd.read_csv(input_csv)
    df['usage_date'] = pd.to_datetime(df['usage_date'])
    df = df.rename(columns={'usage_date': 'ds', 'total_cost': 'y'})

    # Initialize and fit the best Prophet model
    model = Prophet(
        changepoint_prior_scale=0.1,
        seasonality_mode='additive',
        weekly_seasonality=True,
        yearly_seasonality=False,
        daily_seasonality=True,
        growth='linear',
        n_changepoints=25,
        changepoint_range=0.5,
        seasonality_prior_scale=5.0,
        interval_width=0.95,
        uncertainty_samples=2000
    )
    model.add_seasonality(name='24day_cycle', period=24, fourier_order=3)

    model.fit(df)

    # Create future dataframe
    future = model.make_future_dataframe(periods=730)  # 2 years ahead daily

    # Forecast
    forecast = model.predict(future)

    # Save daily forecast
    daily_forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    daily_forecast.to_csv(daily_output_csv, index=False)

    # Aggregate to monthly total forecast
    forecast['month'] = forecast['ds'].dt.to_period('M')
    monthly_forecast = forecast.groupby('month')['yhat'].sum().reset_index()
    monthly_forecast.columns = ['month', 'monthly_total_cost']
    monthly_forecast.to_csv(monthly_output_csv, index=False)

    # Plot results
    last_date = df['ds'].max()
    forecast_in_sample = forecast[forecast['ds'] <= last_date]
    forecast_future = forecast[forecast['ds'] > last_date]

    plt.figure(figsize=(15, 6))

    # Actual observed data
    plt.plot(df['ds'], df['y'], label='Observed (Ground Truth)', color='black')

    # Fitted values
    plt.plot(forecast_in_sample['ds'], forecast_in_sample['yhat'], label='Fitted (Train)', color='green')

    # Forecasted future values
    plt.plot(forecast_future['ds'], forecast_future['yhat'], label='Forecast', color='blue')

    # Confidence interval
    plt.fill_between(forecast_future['ds'],
                     forecast_future['yhat_lower'],
                     forecast_future['yhat_upper'],
                     color='blue', alpha=0.2, label='Confidence Interval')

    # Forecast start vertical line
    plt.axvline(x=last_date, color='gray', linestyle='--', label='Forecast Start')

    plt.title('Prophet Cost Forecast to 2027 with Observed, Fit, and Forecast')
    plt.xlabel('Date')
    plt.ylabel('Total Cost')
    plt.legend()
    plt.tight_layout()
    plt.ylim(-200, 175000)
    plt.grid(True)
    plt.savefig('forecast_plot.png') 
    plt.show()          


def main():
    parser = argparse.ArgumentParser(description='Prophet forecasting for total cost.')
    parser.add_argument('--input', required=True, help='Input CSV file path with usage_date and total_cost.')
    parser.add_argument('--daily_output', required=True, help='Output CSV file path for daily forecasts.')
    parser.add_argument('--monthly_output', required=True, help='Output CSV file path for monthly forecasts.')

    args = parser.parse_args()

    train_and_forecast(args.input, args.daily_output, args.monthly_output)


if __name__ == '__main__':
    main()
