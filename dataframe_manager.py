import pandas as pd
from ib_insync import util

class DF_Manager:
    """Must be connected to ib for bars"""
    """class for managing DataFrame manipulation"""
    def __init__(self, bars, ticker, barsize):
        """Initializing Class Resources"""
        self.ticker = ticker
        self.barsize = barsize
        """Instaniates data from either bars or a dataframe for each time frame"""
        self.create_and_determine_data(bars)

    def create_and_determine_data(self, bars):
        if self.barsize == '5 secs':
            if isinstance(bars, pd.DataFrame):
                self.data_5sec = bars
                self.main_data = self.data_5sec
                self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
                self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
                self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')
            elif isinstance(bars, dict):
                self.data_5sec = [util.df(bars).set_index('date')for symbol, bars in bars.items()]
                self.main_data = self.data_5sec
            else:
                self.data_5sec = util.df(bars)
                self.main_data = self.data_5sec
                self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
                self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
                self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')

        elif self.barsize == '10 secs':
            if isinstance(bars, pd.DataFrame):
                self.data_10sec = bars
                self.main_data = self.data_5sec
                self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
                self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')
            elif isinstance(bars, dict):
                self.data_10sec = [util.df(bars).set_index('date')for symbol, bars in bars.items()]
                self.main_data = self.data_10sec
            else:
                self.data_10sec = util.df(bars)
                self.main_data = self.data_10sec
                self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
                self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')

        elif self.barsize == '1 min':
            if isinstance(bars, pd.DataFrame):
                """Backtests"""
                self.data_1min = bars
                self.main_data = self.data_1min
                self.data_5min = self.convert_to_timeframe(self.data_1min, '5T')
            elif isinstance(bars, dict):
                """using main_multiple.py - multiple tickers"""
                self.data_1min = [util.df(bars).set_index('date') for symbol, bars, in bars.items()]
                self.main_data = self.data_1min
            else:
                """using main.py = strickly only 1 ticker"""
                self.data_1min = util.df(bars)
                self.main_data = self.data_1min
                self.data_5min = self.convert_to_timeframe(self.data_1min, '5T')



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
        self.create_and_determine_data(new_bar)
        # if isinstance(new_bar, dict):
        #     self.determine_main_barsize_dict(new_bar)
        # else:
        #     self.data_5sec = util.df(new_bar)
        #     self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
        #     self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
        #     self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')