from strategies.kefr_kama import Kefr_Kama
from backtest import BackTest
from log import LogBook
from risk_handler import Risk_Handler
from get_data import upload_historical
import numpy as np
import vectorbt as vbt
import datetime
from ib_insync import *
import os

class HyperBT(BackTest):
    """A class to handle Hyper Optimization backtests"""
    def __init__(self, strategy_object):
        """Initiates strategy resources"""
        super().__init__(strategy_object=strategy_object)

    def build_indicator_factory(self):
        """Builds the Indicator Factory"""
        ind = vbt.IndicatorFactory(
            class_name = 'Custom',
            short_name = 'cust',
            input_names = ['open', 'high', 'low', 'close'],
            param_names = ['efratio_timeperiod', 'threshold', 'atr_perc'],
            output_names = ['value']
            ).from_apply_func(
                self.strategy.custom_indicator,
                efratio_timeperiod=14,
                threshold=0.6,
                atr_perc=0.1,
                # param1
                to_2d=False
            )
        return ind
    
    def generate_signals(self):
        """Generates the entries/exits signals"""
        res = self.ind.run(
            self.data.open,
            self.data.high,
            self.data.low,
            self.data.close,
            np.arange(9,22, step=1, dtype=int),
            np.arange(.5, 1.0, step=.1, dtype=float),
            np.arange(.1, 1, step=.1, dtype=float),
            param_product=True
        )
        return res
    
    def graph_data_volume(self):
        """ graphs a 3 parameter hyper optimization backtest"""
        fig = self.returns.vbt.volume(
            x_level = 'cust_efratio_timeperiod',
            y_level = 'cust_threshold',
            z_level = 'cust_atr_perc'
        )
        fig.show()

    def graph_data_heatmap(self):
        """ graphs a 2 parameter hyper optimization backtest"""
        fig = self.returns.vbt.heatmap(
            x_level = 'cust_efratio_timeperiod',
            y_level = 'cust_threshold'
        )
        fig.show()




######################## Below is code to run Hyper Optimized backtest ####################


#tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG', 'SGMT', 'ELAB', 'SPRC']




def run_hyper():
    """NOTE: update later so that it gets datetime by itself instead of manually inserting the date"""
    ##################### data for hyper ####################################
    df_object_list = upload_historical()
    """
    below is how we need to struture our data so that we can hyper optimize
    for all our tickers

    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=2)
    btc_price = vbt.YFData.download(
        ['BTC-USD', 'ETH-USD'],
        missing_index = 'drop',
        start = start_time,
        end = end_time,
        interval = '1m').get('Close')
    print(btc_price)
    """
    
    risk = Risk_Handler(ib = None,
                        perc_risk = 0.8,
                        stop_time="10:00:00-05:00",
                        atr_perc = .20)

    # iterating of each DF_Manager and creating a strategy object with each manager
    logbook = LogBook(None, None)
    for i, manager in enumerate(df_object_list):
        print(f"---------------------------{manager.ticker}---------------------------------------")
        if i == 0:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize= "1min",
                risk = risk)
            backtest = HyperBT(strat)
            logbook = LogBook(ib=None, value=backtest)
        else:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize='1min',
                risk=risk)
            backtest = HyperBT(strat)
            logbook.insert_beginning(new_value=backtest)

        #print(backtest.returns)
        #print(type(backtest.returns))
        #df= backtest.returns.reset_index()
        #df.columns = ['cust_efratio_timeperiod', 'cust_threshold', 'cust_atr_perc', 'return']
        #print(df)
        #print(backtest.returns.max())
        #print(backtest.returns.idxmax())
        backtest.graph_data_volume()

        
    return logbook


def test_multiple_tickers():
    """NOTE: update later so that it gets datetime by itself instead of manually inserting the date"""
    ##################### data for hyper ####################################
    df_object_list = upload_historical()
    """
    below is how we need to struture our data so that we can hyper optimize
    for all our tickers

    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=2)
    btc_price = vbt.YFData.download(
        ['BTC-USD', 'ETH-USD'],
        missing_index = 'drop',
        start = start_time,
        end = end_time,
        interval = '1m').get('Close')
    print(btc_price)
    """
    
    risk = Risk_Handler(ib = None,
                        perc_risk = 0.8,
                        stop_time="10:00:00-05:00",
                        atr_perc = .20)

    # iterating of each DF_Manager and creating a strategy object with each manager
    logbook = LogBook(None, None)
    for i, manager in enumerate(df_object_list):
        print(f"---------------------------{manager.ticker}---------------------------------------")
        if i == 0:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize= "1min",
                risk = risk)
            backtest = HyperBT(strat)
            logbook = LogBook(ib=None, value=backtest)
        else:
            strat = Kefr_Kama(
                df_manager=manager,
                barsize='1min',
                risk=risk)
            backtest = HyperBT(strat)
            logbook.insert_beginning(new_value=backtest)

        #print(backtest.returns)
        #print(type(backtest.returns))
        #df= backtest.returns.reset_index()
        #df.columns = ['cust_efratio_timeperiod', 'cust_threshold', 'cust_atr_perc', 'return']
        #print(df)
        #print(backtest.returns.max())
        #print(backtest.returns.idxmax())
        backtest.graph_data_volume()

        
    return logbook




logbook = run_hyper()
logbook.export_hyper_to_db('KEFR_risk')