import pandas as pd
import os
import datetime


def read_historical_prices_eur_demo():
    df = pd.read_csv(os.path.join("demo", "demo_static_data", "historical_prices_eur.csv"), index_col='Gmt time', parse_dates=True)
    df.index = df.index.to_series().apply(lambda x: x.date())    
    return df


HISTORICAL_PRICES_EUR_DEMO = read_historical_prices_eur_demo()


def get_historical_prices_eur_demo_shifted():
    df = HISTORICAL_PRICES_EUR_DEMO.copy()
    last_date_in_df = pd.Timestamp(df.index.max())
    current_date = pd.Timestamp(datetime.date.today())
    delta = current_date - last_date_in_df
    df.index = df.index + delta    
    return df


def get_prices_daily(instrument, quote_currency, timespan_end, timespan=datetime.timedelta(days=0)):
    if instrument == quote_currency:
        timespan_start = timespan_end - timespan

        if timespan == datetime.timedelta(days=0):
            values = pd.Series([1], index=pd.Index([timespan_end], name="date"), name=instrument)
        else:
            date_range = pd.date_range(timespan_start, timespan_end, freq="D").to_series().apply(lambda x: x.date())
            values = pd.Series(1, index=pd.Index(date_range, name="date"), name=instrument)

    else:
        data = get_historical_prices_eur_demo_shifted()

        timespan_start = timespan_end - timespan

        if quote_currency != "EUR":
            raise Exception(f"Only static demo market data is available. (quote_currency={quote_currency})")

        if instrument not in data.columns:
            raise Exception(f"Only static demo market data is available. (instrument={instrument})")

        if timespan_end not in data.index:
            raise Exception(f"Only static demo market data is available. (timespan_end={timespan_end})")

        if timespan_start not in data.index:
            raise Exception(f"Only static demo market data is available. (timespan_start={timespan_start})")

        values = data[instrument].loc[timespan_start:timespan_end]
        values.index.name = "date"

    return values
