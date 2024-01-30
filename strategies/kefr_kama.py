"""
Strategy using Kuafman Efficiency Ratio and Kaufmans Adaptive Moving Average
"""
from strategies.strategy import Strategy
import plotly.graph_objects as go
import pandas as pd
import talib as ta

class Kefr_Kama(Strategy):
    def __init__(self, df_manager, risk=None, barsize=None):
        """Initiate class resources"""
        super().__init__(df_manager = df_manager, risk=risk, barsize=barsize)
    
    def custom_indicator(self, open, high, low, close, efratio_timeperiod=10, threshold=0.5, atr_perc = .2):
        """Actual strategy to be used"""
        self.risk.atr_perc = atr_perc
        #print(f'\nefraiot:{efratio_timeperiod}, threshold:{threshold}')
        # entrys
        efratios = self.calculate_efratio(efratio_timeperiod)
        signals = pd.Series(0, index=efratios.index)
        signals[efratios > threshold] = 1

        # exits
        if self.risk:
            if self.risk.stop_time is not None:
                signals = self._stop_trading_time(signals)
            atr = ta.ATR(high, low, close, timeperiod=14)

            # will have to re-anable this if connect to IB
            if self.risk.ib is not None:
                if self.risk.ib.positions():
                    signals = self._process_atr_data(signals, atr, close, high)
            else:
                signals = self._process_atr_data(signals, atr, close, high)
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
        else:
            return signals
        
        return signals

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