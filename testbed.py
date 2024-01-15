from ib_insync import *
#from scanner import Scanner
#from sec_data import SEC_Data
#from risk_handler import Risk_Handler
#from dataframe_manager import DF_Manager
from strategies.engulfing_risk.strategy import Strategy
from strategies.engulfing_risk.backtest import BackTest
from risk_handler import Risk_Handler
from get_data import upload_historical

# tickers to backtest
tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG']

df_object_list = upload_historical(tickers=tickers_list)

risk = Risk_Handler(ib = None,
                    perc_risk = 0.8,
                    stop_time="11:30:00-05:00",
                    atr_perc = .1)

# iterating of each DF_Manager and creating a strategy object with each manager
for i, manager in enumerate(df_object_list):
    # 
    strat = Strategy(
        df_manager=manager,
        barsize= "1min",
        risk = risk)
    backtest = BackTest(strat)

    print(f"\n\n------------------------{tickers_list[i]}--------------------------")
    print(backtest.pf.stats())
    backtest.graph_data()
    