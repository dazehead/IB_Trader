import pandas as pd
from ib_insync import util

class DF_Manager:
    """Must be connected to ib for bars"""
    """class for managing DataFrame manipulation"""
    def __init__(self, bars, ticker):
        """Initializing Class Resources"""
        self.ticker = ticker
        """Instaniates data from either bars or a dataframe for each time frame"""
        if isinstance(bars, pd.DataFrame):
            self.data_5sec = bars
        else:
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
        """Updates new 5 sec data"""
        """NEED TO PUT SOMETHING IN SO THAT 5 SECOND CLOSE IS NOT BEING USED AS
        THE 1 MIN CLOSE WHILE THE BAR IS BETWEEN THE MINUTE SPAN
        ---OR JUST DO A 1 MINUTE BAR WE MIGHT GET IN A BIND IF WE DO THAT BECAUSE
        STOP LOSS MIGHT TANK DURING A 1 MINUTE BAR- IF WE WANT IT TO BE TRUE TO A BACKTEST
        THEN WE MUST BE WILLING TO TAKE THAT RISK OF NOT DOING ANYTHING UNTIL THE 1 MINUTE
        BAR UPDATES"""
        self.data_5sec = util.df(new_bar)
        self.data_10sec = self.convert_to_timeframe(self.data_5sec, '10S')
        self.data_1min = self.convert_to_timeframe(self.data_5sec, '1T')
        self.data_5min = self.convert_to_timeframe(self.data_5sec, '5T')