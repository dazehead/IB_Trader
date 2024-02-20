"""
Strategy using Kuafman Efficiency Ratio and Kaufmans Adaptive Moving Average
"""
from strategies.strategy import Strategy
import plotly.graph_objects as go
import pandas as pd
import talib as ta
import numpy as np
import math

class Kefr_Kama(Strategy):
    def __init__(self, df_manager, risk=None, barsize=None):
        """Initiate class resources"""
        super().__init__(df_manager = df_manager, risk=risk, barsize=barsize)
        self.volume = df_manager.data_10sec.volume
        self.kama = None


    def active_buy_monitor(self, close, open):
        print(self.volume)
        prev_close = close[-2]
        prev_open = open[-2]
        current_close = close[-1]
        current_open = open[-1]

        # if the last 2 bars are green
        if prev_close < current_close and prev_open < prev_close and current_open < current_close:
            result = 1
            self.risk.started_buy_monitoring = False
        else:
            result = 0 

        return result
    
    def calculate_kama(self, efratios, close):
        fast_period = 30
        slow_period = 3
        fast_ma = ta.EMA(close, timeperiod=fast_period)
        slow_ma = ta.EMA(close, timeperiod=slow_period)
        # fast_ma has unstable period equal to fast_period
        kama = []
        for i in range(len(close)):
            if i < fast_period:
                kama.append(np.NaN)
            else:                          #print(sc)
                if i == fast_period:
                    kama.append(close[i])
                else:
                    fastest = (2/(fast_ma[i] + 1))
                    slowest = (2/(slow_ma[i] + 1))
                    mapping = {i:2-0.043 * (i-1) for i in range(1,21)}
                    key = int(round(close[i],0))
                    if key > 20:
                        key = 20
                    k = 60
                    n = mapping[key]
                    #print(n)
                    x = k/ close[i]**n
                    #print(x)
                    sc = (efratios[i] * (fastest - slowest) + slowest)**x
                    kama.append(kama[-1] + sc * (close[i] - kama[-1]))
        return kama
    
    def process_kama(self, signals, close):
        new_signals = []
        for i in range(len(signals)):
            if signals[i] == 1:
                if close[i] > self.kama[i]:
                    new_signals.append(1)
                else:
                    new_signals.append(0)
            else:
                new_signals.append(0)
        new_signals - pd.Series(new_signals, index=signals.index)

        return new_signals
    
    def simple_atr_process(self, signals, atr, close):

        if self.risk.ib is not None:
            """if we are connected to IB"""
            self.risk.stop_loss = self.kama[-1] - atr[-1]

            if close[-1] < self.risk.stop_loss:
                """SELL"""
                new_signals = signals
                new_signals[-1] = -1
            elif close[-1] > self.risk.stop_loss:
                new_signals = signals
        else:
            """If we are only backtesting and NOT connected to IB"""
            stop_index = np.where(~np.isnan(atr))[0][0]
            zeros_array = np.zeros_like(signals)
            is_trading = signals[stop_index:]
            not_trading = zeros_array[:stop_index]
            new_signals = np.concatenate((is_trading, not_trading))

            in_trade = False
            for i,price in enumerate(close):
                try:
                    price = close[i+14]
                    #print(f"------------------------{i}------------------------")
                    # skips until atr has values populated
                    if np.isnan(atr[i]):
                        pass
                    else:
                        self.risk.stop_loss = self.kama[i] - atr[i]
                        if new_signals[i] == 1 and not in_trade:
                            print(i, price, self.kama[i], price > self.kama[i])  
                            if price > self.kama[i]:
                            # assigns the price of stock during a BUY signal 
                                in_trade = True
                                print('BUY')
                                print(i, new_signals[i], price, self.kama[i], price > self.kama[i])
                            else:
                                new_signals[i] = 0
                        elif in_trade:
                            if price < self.risk.stop_loss:
                                """SELL"""
                                new_signals[i] = -1
                                in_trade = False
                            elif price > self.risk.stop_loss:
                                new_signals[i] = 0

                except IndexError:
                    pass
            #add 14 zeros to the front of atr
            temp_signals = new_signals[:-14]
            new_signals = np.concatenate((np.zeros(14), temp_signals))

        return new_signals


    def custom_indicator(self, open, high, low, close, efratio_timeperiod=3, threshold=0.5, atr_perc = 1.2):
        """Actual strategy to be used"""
        self.risk.atr_perc = atr_perc
        # entrys
        efratios = self.calculate_efratio(efratio_timeperiod)
        #print(efratios)
        """insert KAMA here"""
        kama = self.calculate_kama(efratios, close)
        self.kama = pd.Series(kama, index=efratios.index)
        signals = pd.Series(0, index=efratios.index)
        signals[efratios > threshold] = 1

        signals = self.process_kama(signals, close)

        # trading times
        if self.risk:
            if self.risk.stop_time is not None:
                signals = self._stop_trading_time(signals)
            if self.risk.start_time is not None:
                signals = self._start_trading_time(signals)

            # exits
            atr = ta.ATR(high, low, close, timeperiod=14)
            if self.risk.ib is not None:
                if self.risk.ib.positions():
                    self.simple_atr_process(signals, atr, close)
                    #signals = self._process_atr_data(signals, atr, close, high)

                    # active buy monitoring function logic
                if self.risk.active_buy_monitoring:
                    if signals[-1] == 1 and not self.risk.started_buy_monitoring:
                        self.risk.started_buy_monitoring = True
                        print('********** ACTIVE BUY MONITORING ENABLED **********')
                        signals[-1] = 0
                    elif self.risk.started_buy_monitoring and signals[-1] != -1:
                        result = self.active_buy_monitor(close, open)
                        signals[-1] = result


            else:
                if self.risk.active_buy_monitoring:
                    signals = self._process_buy_monitoring(signals=signals, close=close, open=open)
                signals = self.simple_atr_process(signals, atr, close)
                #signals = self._process_atr_data(signals, atr, close, high)
                signals = self._process_signal_data(signals=signals)
                #print(f"atr signals: {signals[-1]}")


                #--------------------------Testing------------------------
                """
                print(len(signals_with_efr))
                graph_signals = pd.Series(signals_with_efr, index=self.data_1min.index)
                self.graph_data(graph_signals, efratio_timeperiod, efratios, 'Signals with EFR')

                print(len(signals_after_atr))
                graph_signals = pd.Series(signals_after_atr, index=self.data_1min.index)
                self.graph_data(graph_signals, efratio_timeperiod, efratios, 'Signals after ATR')

                print(len(final_signals))
                graph_signals = pd.Series(final_signals, index=self.data_1min.index)
                self.graph_data(graph_signals, efratio_timeperiod, efratios, 'final_signals')
                """        
        return signals

    def _process_buy_monitoring(self,signals, close, open):
        """Helper function to proccess active buy monitoring data"""

        new_signals = []
        monitoring = False
        for i in range(len(signals)):
            current_volume = self.volume[i]
            prev_volume = self.volume[i-1]
            if signals[i] == 1 and not monitoring:
                monitoring = True
                new_signals.append(0)
            elif monitoring and signals[i] != -1:
                if open[i-1] < close[i-1] and open[i] < close[i] and close[i-1] < close[i]:
                    new_signals.append(1)
                    monitoring = False
                else:
                    new_signals.append(0)
            else:
                new_signals.append(signals[i])
        return new_signals





    def _efratio(self, prices):
        """Helper function to calculate single Effecincy Ratio"""
        #print(self.data_1min.close)

        #Calculate price changes and absolute price changes
        price_changes = [prices[i]-prices[i-1] for i in range(1, len(prices))]
        absolute_price_changes = [abs(change) for change in price_changes]

        # Calculate net price change and sum of absolute price changes
        net_price_change = prices[-1] - prices[0]
        #print(net_price_change)
        sum_absolute_price_changes = sum(absolute_price_changes)
        #print(sum_absolute_price_changes)

        if sum_absolute_price_changes == 0:
            return 0
        
        kaufman_ratio = net_price_change / sum_absolute_price_changes

        return round(kaufman_ratio, 3)
    
    def calculate_efratio(self, time_period):
        """Logic to calculate Effieciency Ratio """
        efratios = []
        close_prices = self.data_1min.close

        for i in range(len(close_prices) - time_period + 1):
            window_prices = close_prices[i:i + time_period]

            window_efratio = self._efratio(window_prices)

            efratios.append(window_efratio)

        zeros = [0 for i in range(time_period-1)]
        efratios = zeros + efratios
        efratios = pd.Series(efratios, index=self.data_1min.index)
        return efratios
    
    def graph_data(self, data, time_period, efratios, name):
        """Function to graph data"""
        ########### Graphing for Visualization #################################
        #fig1 = data.vbt.ohlcv.plots(settings=dict(plot_type='candlestick'))
        #fig1.show()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=efratios.index,
                         y=efratios,
                         mode='lines',
                         name=f'Efficiency Ratios ({time_period}-day window)',
                         line=dict(color='red')))
        fig2.show()

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=data.index,
                                  y=data,
                                  mode='lines',
                                  name=name,
                                  line=dict(color='red')))
        fig3.show()