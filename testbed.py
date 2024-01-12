from ib_insync import *
#from scanner import Scanner
#from sec_data import SEC_Data
#from risk_handler import Risk_Handler
#from dataframe_manager import DF_Manager
from strategies.test.strategy import Strategy
from strategies.test.backtest import BackTest
from risk_handler import Risk_Handler
from get_data import upload_historical
from dataframe_manager import DF_Manager

tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG']

df_object_list = upload_historical(tickers=tickers_list)

risk = Risk_Handler(stop_time="10:00:00-05:00")

# iterating of each DF_Manager and creating a strategy object with each manager
for i, manager in enumerate(df_object_list):
    # 
    strat = Strategy(
        df_manager=manager,
        barsize= "10sec",
        risk = risk)
    backtest = BackTest(strat)

    print(f"\n\n------------------------{tickers_list[i]}--------------------------")
    print(backtest.pf.stats())
    backtest.graph_data()
    