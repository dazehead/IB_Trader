"""
Strategy class
"""
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib as ta
from ib_insync import *
import sys

class Strategy:
    """Class to store strategy resources"""
    def __init__(self, df_manager, risk=None, barsize=None):
        if barsize is None:
            print("You need to define barsize")
            sys.exit()

        """Initialize different bar data"""
        self.ticker = df_manager.ticker
        self.risk = risk
        self.barsize = barsize
        #print("...Initializing Stategy")
        self.data_5sec = df_manager.data_5sec
        self.data_10sec = df_manager.data_10sec
        self.data_1min = df_manager.data_1min
        self.data_5min = df_manager.data_5min
        self.final_signals = None
        #print("...Strategy Initialized")

    def custom_indicator(self, open, high, low, close):
        """Actual Strategy to be used"""
        #Pattern Recognition
        strat = ta.CDLENGULFING(open, high, low, close)
        signals = self._process_ta_pattern_data(strat)
        #print(f"Engulfing signals: {signals[-1]}")
        if self.risk:
            if self.risk.stop_time is not None:
                signals = self._stop_trading_time(signals)
            atr = ta.ATR(high, low, close, timeperiod=14)
            signals = self._process_atr_data(signals, atr, close, high)
            #print(f"Processed ATR signals: {signals[-1]}")

        signals = self._process_signal_data(signals)
        
        # Technical Indicators
        #rsi = vbt.RSI.run(close, window = rsi_window).rsi.to_numpy()# converting to numpy array
        #entry_condition = (rsi > 50)
        #exit_condition = (rsi < 30)
        #signals = np.where(entry_condition, 1, np.where(exit_condition, -1, 0))
        #signals = self._process_signal_data(signals)
        #print(signals) # check if signals data is correct
        self.final_signals = signals
        return signals

    def _process_atr_data(self, signals, atr, close, high):
        """Replaces atr nan with 0's on signals and calculates stop loss and profit target
        impements them into new_signals"""
        # need to get price from order execution
        #stop_index = np.where(~np.isnan(atr))[0][0]
        #zeros_array = np.zeros_like(signals)
        #is_trading = signals[stop_index:]
        #not_trading = zeros_array[:stop_index]
        #new_signals = np.concatenate((is_trading, not_trading))
        price_at_purchase = self.risk.ib.positions()[-1].avgCost
        if self.risk.highest_high is None:
            self.risk.highest_high = high[-1]
            new_signals = signals
        else:
            if price_at_purchase > self.risk.highest_high:
                self.risk.highest_high = price_at_purchase
            if high[-1] > self.risk.highest_high:
                self.risk.highest_high = high[-1]
            

            stop_loss = self.risk.highest_high - (atr[-1] + self.risk.atr_perc)
            print(f"High: {self.risk.highest_high}")
            print(f"ATR: {atr[-1]}")
            print(f"Purchase Price: {price_at_purchase}")
            print(f"ATR perc_risk = {self.risk.atr_perc}")
            print(f"STOPLOSS: {stop_loss}")
            if close[-1] < stop_loss:
                """SELL"""
                new_signals = signals
                new_signals[-1] = -1
            elif close[-1] > stop_loss:
                new_signals = signals


        return new_signals
        

    def _process_ta_pattern_data(self, signals):
        """Helper function to process signals generated through TA-LIB"""
        signals[signals == 100] = 1
        signals[signals == -100] = -1
        return signals

    def _process_signal_data(self, signals): # only use for backtest
        """Helper function to process signals so that Buy and Hold until sell signal"""
        """This might need to be deleted when live trading it does not allow for a Trade"""
        """to go through if the backtest shows 1 at the beginning of the day"""
        in_trade = False

        for i in range(len(signals)):
            if signals[i] == 1:
                if not in_trade:
                    in_trade = True
                else:
                    signals[i] = 0
            elif signals[i] == -1 and not in_trade:
                signals[i] = 0
            elif signals[i] == -1:
                in_trade = False

        return signals
    
    def _stop_trading_time(self, signals):
        #print("\n****************************")
        if self.barsize == '10sec':
            datetimes = self.data_10sec.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_10sec
        elif self.barsize == '1min':
            datetimes = self.data_1min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_1min
        elif self.barsize == '5min':
            datetimes = self.data_5min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
            data = self.data_5min

        zeros_array = np.zeros_like(signals)
        stop_index = (datetimes == date).argmax()
        trading_time_array = signals[:stop_index]
        stop_trading_array = zeros_array[stop_index:]
        new_signals = np.concatenate((trading_time_array, stop_trading_array))

        return new_signals


'''
    def graph_data(self, data):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        fig = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig.show()
'''