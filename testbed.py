from ib_insync import *
from strategies.engulfing import Engulfing
from backtest import BackTest
from risk_handler import Risk_Handler
from get_data import upload_historical
from log import LogBook
from scanner import Scanner

# CONSTANTS
tickers_list = ['LBPH', 'NEXI', 'MINM', 'AIMD', 'ACON', 'SNTG']


def run_backtest(tickers_list):
    df_object_list = upload_historical(tickers=tickers_list)

    risk = Risk_Handler(ib = None,
                        perc_risk = 0.8,
                        stop_time="10:00:00-05:00",
                        atr_perc = .1)

    # iterating of each DF_Manager and creating a strategy object with each manager
    logbook = None
    for i, manager in enumerate(df_object_list):
        if i == 0:
            strat = Engulfing(
                df_manager=manager,
                barsize= "1min",
                risk = risk)
            backtest = BackTest(strat)
            logbook = LogBook(backtest)
        else:
            strat = Engulfing(
                df_manager=manager,
                barsize='1min',
                risk=risk)
            backtest = BackTest(strat)
            logbook.insert_beginning(backtest)
        #print(list(dir(backtest.pf)))
        #print(backtest.pf.stats())
        #backtest.graph_data()
    return logbook
#logbook.export_backtest_data("logbooks/backtests_01152024.csv")
#logbook = run_backtest(tickers_list=tickers_list)
#df = logbook._convert_to_dataframe()
#print(df)


class Test_Scanner(Scanner):
    def __init__(self, ib, scancode):
        super().__init__(ib=ib, scancode=scancode)
       



def test_scanner():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=2)
    
    top_gainers = Test_Scanner(ib, 'TOP_PERC_GAIN')
    print(top_gainers.tickers_list)
    top_gainers.scan_news()
    print(top_gainers.tickers_list)
    #top_gainers.retreive_filter_params()

test_scanner()

