from strategies.kefr_kama import Kefr_Kama
import plotly.graph_objects as go
import pandas as pd
import talib as ta
import numpy as np
import math
import time
from numba import njit


class Kama_Short(Kefr_Kama):
    def __init__(self, df_manager, risk=None, barsize=None, index=None):
        """we have inversed the ATR to add instead of subtract and took the difference from close and added it to close"""
        super().__init__(df_manager=df_manager, risk=risk, barsize=barsize, index=index)
        self.kama2 = None

    def simple_atr_process(self, signals, atr, close):
        print('---simple atr process')
        if self.risk.ib is not None:
            """if we are connected to IB"""
            self.risk.stop_loss[self.ticker] = close[-1] + (close[-1] - round(self.kama[-1] + atr[-1] * self.risk.atr_perc, 2))
            print(f'---Stop Loss: {self.risk.stop_loss[self.ticker]}')
            if close[-1] <= self.risk.stop_loss[self.ticker]:
                print('----COVER SELL SIGNAL')
                """BUY"""
                new_signals = signals
                new_signals[-1] = -1
            elif close[-1] < self.risk.stop_loss[self.ticker]:
                print('----NOTHING SIGNAL')
                new_signals = signals
        else:
            """If we are only backtesting and NOT connected to IB"""
            stop_index = np.where(~np.isnan(atr))[0][0]
            zeros_array = np.zeros_like(signals)
            is_trading = signals[stop_index:]
            not_trading = zeros_array[:stop_index]
            new_signals = np.concatenate((is_trading, not_trading))
            self.risk.stop_loss = None

            in_trade = False
            for i,price in enumerate(close):
                try:
                    price = close[i+14]
                    #print(f"------------------------{i}------------------------")
                    # skips until atr has values populated
                    if np.isnan(atr[i]):
                        pass
                    else:
                        self.risk.stop_loss = close[-1] + (close[-1] -(self.kama[i] + atr[i] * self.risk.atr_perc))
                        if new_signals[i] == 1 and not in_trade:
                            #print(i, price, self.kama[i], price > self.kama[i])  
                            if price > self.kama[i]:
                            # assigns the price of stock during a BUY signal 
                                in_trade = True
                                #print('BUY')
                                #print(i, new_signals[i], price, self.kama[i], price > self.kama[i])
                            else:
                                new_signals[i] = 0
                        elif in_trade:
                            if price > self.risk.stop_loss:
                                """BUY COVER SELL"""
                                new_signals[i] = -1
                                in_trade = False
                            elif price < self.risk.stop_loss:
                                new_signals[i] = 0

                except IndexError:
                    pass
            #add 14 zeros to the front of atr
            temp_signals = new_signals[:-14]
            new_signals = np.concatenate((np.zeros(14), temp_signals))

        return new_signals
    
    def calculate_kama(self, efratios, close):
        fast_period = 30
        slow_period = 3

        fast_ma = ta.EMA(close, timeperiod=fast_period)
        slow_ma = ta.EMA(close, timeperiod=slow_period)

        kama = np.full_like(close, np.nan)  # Initialize kama array with NaNs
        kama2 = kama

        # Calculate KAMA using vectorized operations
        fastest = (2 / (fast_ma + 1))
        slowest = (2 / (slow_ma + 1))

        mapping = {i: 2 - 0.043 * (i - 1) for i in range(1, 21)}
        keys = np.minimum(np.round(close), 20).astype(int)
        n_values = np.array([mapping[key] for key in keys])

        k = 60
        x = k / np.power(close, n_values)

        sc = (efratios * (fastest - slowest) + slowest) ** x

        kama[fast_period - 1] = close[fast_period - 1]  # Set initial value for kama
        kama2[fast_period -1] = close[fast_period - 1]

        for i in range(fast_period, len(close)):
            kama[i] = kama[i - 1] + sc[i] * (close[i] - kama[i - 1]) + .09#####added this
            kama2[i] = kama2[i-1] + sc[i] * (close[i] - kama[i - 1])


        return kama, kama2
    
    def custom_indicator(self, open, high, low, close, efratio_timeperiod=6, threshold=0.9, atr_perc = .6):
        """Actual strategy to be used"""
        #start = time.time()
        self.risk.atr_perc = atr_perc
        # entrys
        efratios = self.calculate_efratio(efratio_timeperiod)
        #print(efratios)
        """insert KAMA here"""
        print('---calculating KAMA')
        try:
            kama, kama2 = self.calculate_kama(efratios, close)
            self.kama = pd.Series(kama, index=efratios.index)
            self.kama2 = pd.Series(kama2, index=efratios.index)

            print(self.kama)
            print(self.kama2)

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
                        """ASSIGNS THE STOP LOSS TO RISK.STOPLOSS, THIS COULD BE ALL WE WANT"""
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
            #print(f"Total Time Elapsed: {time.time() - start}")
        except IndexError:
            print('Not enough data to calculate KAMA')
            signals = 0
        return signals