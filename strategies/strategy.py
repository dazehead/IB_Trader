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
        """Initialize Class Resources"""
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
            if self.risk.start_time is not None:
                signals = self._start_trading_time(signals)
            atr = ta.ATR(high, low, close, timeperiod=14)
            signals = self._process_atr_data(signals, atr, close, high)
            #print(f"Processed ATR signals: {signals[-1]}")

        signals = self._process_signal_data(signals)
        
        """
        #Technical Indicators
        rsi = vbt.RSI.run(close, window = rsi_window).rsi.to_numpy()# converting to numpy array
        entry_condition = (rsi > 50)
        exit_condition = (rsi < 30)
        signals = np.where(entry_condition, 1, np.where(exit_condition, -1, 0))
        signals = self._process_signal_data(signals)
        print(signals) # check if signals data is correct
        """
        return signals

    def _process_atr_data(self, signals, atr, close, high):
        """Replaces atr nan with 0's on signals and calculates stop loss and profit target
        impements them into new_signals"""
        """ ALSO IMPLEMENTED IS A PROFIT TARGET ESTIMATION"""

        if self.risk.ib is not None:
            """if we are connected to IB"""
            price_at_purchase = self.risk.ib.positions()[-1].avgCost
            if self.risk.highest_high is None:
                self.risk.highest_high = close[-1]
                new_signals = signals
            else:
                if price_at_purchase > self.risk.highest_high:
                    self.risk.highest_high = price_at_purchase
                if close[-1] > self.risk.highest_high:
                    self.risk.highest_high = close[-1]
                

                self.risk.stop_loss = round(self.risk.highest_high - (atr[-1]*2 + self.risk.atr_perc), 2)
                print(f"Highest Close: {self.risk.highest_high}")
                #print(f"ATR: {atr[-1]}")
                print(f"Purchase Price: {price_at_purchase}")
                #print(f"ATR perc_risk = {self.risk.atr_perc}")
                print(f"Stop Loss: {self.risk.stop_loss}")
                if close[-1] < self.risk.stop_loss:
                    """SELL"""
                    new_signals = signals
                    new_signals[-1] = -1
                elif close[-1] > self.risk.stop_loss:
                    new_signals = signals
        else:
            """If we are only backtesting and NOT connect to IB"""
            stop_index = np.where(~np.isnan(atr))[0][0]
            zeros_array = np.zeros_like(signals)
            is_trading = signals[stop_index:]
            not_trading = zeros_array[:stop_index]
            new_signals = np.concatenate((is_trading, not_trading))

            in_trade = False
            price_at_purchase = None
            new_high = None
            for i,price in enumerate(close):
                try:
                    price = close[i+14]
                    #print(f"------------------------{i}------------------------")
                    # skips until atr has values populated
                    if np.isnan(atr[i]):
                        pass
                    else:
                        if new_signals[i] == 1 and not in_trade:
                            # assigns the price of stock during a BUY signal 
                            price_at_purchase = price
                            new_high = price#high[i+14]
                            in_trade = True
                            #print("BUY")
                        if in_trade:
                            # in a trade and new_high-current highest is less than the current high
                            if new_high < price:#high[i+14]:
                                # the new high is the current price
                                new_high = price#high[i+14]
                            
                            """Below code for a percentage based atr """
                            #self.risk.stop_loss = new_high - (price_at_purchase * (atr[i] + self.risk.atr_perc))
                            #profit_target = price_at_purchase + (price_at_purchase * (atr[i] + self.risk.profit_target_perc))
                            
                            """Below code for subtracting the atr"""
                            self.risk.stop_loss = round(new_high - (atr[i]*2 + self.risk.atr_perc), 2)
                            profit_target = price_at_purchase + (atr[i] + self.risk.atr_perc)

                            #print(f"PROFIT TARGET: {profit_target}")
                            #print(f"STOP LOSS: {self.risk.stop_loss}")
                            #print(f"PRICE: {price}")
                            #print(f"NEW HIGH: {new_high}")
                            if price < self.risk.stop_loss:
                                # hit our stop loss need to SELL
                                new_signals[i] = -1
                                in_trade = False
                                #print(f"PROFIT TARGET: {profit_target}")
                                #print(f"STOP LOSS: {self.risk.stop_loss}")
                                #print(f"PRICE: {price}")
                                #print(f"NEW HIGH: {new_high}")
                                #print("SELL\n")
                            elif new_signals[i] == -1 and price > self.risk.stop_loss and price < profit_target:
                                # SELL signal but stop loss not hit and profit target not hit: keep going
                                #print("PROFIT NOT HIT AND STOP LOSS NOT HIT")              
                                new_signals[i] = 0
                            elif (price > profit_target) and (new_signals[i] == -1):
                                pass
                                # logic for if price is above profit target and a SELL signal occurs
                                #in_trade = False
                                #print("PRICE ABOVE PROFIT TARGET AND SELL SIGNALS ---- DO NOTHING")
                except IndexError:
                    pass
            #add 14 zeros to the front of atr
            temp_signals = new_signals[:-14]
            new_signals = np.concatenate((np.zeros(14), temp_signals))

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
        if self.barsize == '10sec':
            datetimes = self.data_10sec.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
        elif self.barsize == '1min':
            datetimes = self.data_1min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")
        elif self.barsize == '5min':
            datetimes = self.data_5min.index
            date = pd.to_datetime(f"{str(datetimes[0]).split()[0]} {self.risk.stop_time}")

        stop_index = (datetimes == date).argmax()

        new_signals = signals.copy()
        new_signals[stop_index:] = 0

        return new_signals
    
    def _start_trading_time(self, signals):
        start_time = self.risk.start_time

        if self.barsize == '10sec':
            datetimes = self.data_10sec.index
            data = self.data_10sec
        elif self.barsize == '1min':
            datetimes = self.data_1min.index
            data = self.data_1min
        elif self.barsize == '5min':
            datetimes = self.data_5min.index
            data = self.data_5min

        date_str = f"{str(datetimes[0]).split()[0]} {start_time}"
        date = pd.to_datetime(date_str)
        start_index = np.argmax(datetimes == date)

        new_signals = np.zeros_like(signals)
        new_signals[start_index:] = signals[start_index:]

        return new_signals



    def graph_data(self, data):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        fig = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        fig.show()
