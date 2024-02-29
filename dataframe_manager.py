import pandas as pd
from ib_insync import util

class DF_Manager:
    """Must be connected to ib for bars"""
    """class for managing DataFrame manipulation"""
    def __init__(self, bars, ticker):
        """Initializing Class Resources"""
        self.ticker = ticker
        """Instaniates data from either bars or a dataframe for each time frame"""
        if isinstance(bars, pd.DataFrame): # for backtests
            self.data_5sec = bars
        elif isinstance(bars, dict): # for multiple tickers
            self.data_5sec = [util.df(bars).set_index('date')for symbol, bars in bars.items()]
            #print(self.data)

        else: # for a single ticker
            self.data_5sec = util.df(bars)
            self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
            self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
            self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')

    def convert_to_timeframe(self,dataframe, timeframe):
        """Converts dataframe into different timeframes"""
        # Set the 'date' column as the index
        dataframe = dataframe.set_index('date')
        
        # Resample the DataFrame based on the specified timeframe
        resampled_df = dataframe.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'average': 'last',
            'barCount': 'sum'
        })
        
        # Drop rows with NaN values
        resampled_df = resampled_df.dropna()
        
        return resampled_df

    def update(self, new_bar):
        """Updates new data"""
        if isinstance(new_bar, dict):
            self.data_5sec = [util.df(bars).set_index('date') for symbol, bars in new_bar.items()]
        else:
            self.data_5sec = util.df(new_bar)
        self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
        self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
        self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')