import time
from datetime import datetime, timedelta
from ib_insync import *

class Trade:
    def __init__(self, ib, risk, signals, contract, counter=None):
        self.ib = ib
        self.risk = risk
        self.top_stock = contract
        self.all_signals = signals

        self.todays_date = str(datetime.now()).split(' ')[0]
        self.outside_rth = self.check_RTH()

        if counter is not None:
            self.signal = signals[counter]
        else:
            self.signal = signals[-1]
        

    def execute_trade(self):
        """need functionality for if we bought ORTH and are selling RTH"""
        price = self.ib.reqMktData(self.top_stock,'', False, False).marketPrice()
        num_shares = self.risk.balance_at_risk // price

        if not self.ib.positions() and self.signal == 1:
            self._buy_order(num_shares)
        elif self.ib.positions() and (self.signal == -1):
            """might have to tweek this possible it will not sell everything and we will have to update the order"""
            self._sell_order()
        else:
            """this section is to make sure that all positions were sold if not cancel and put in another market order"""
            self._check_order()
    
    def _buy_order(self, num_shares):
        buy_order = MarketOrder('BUY', num_shares)
        buy_order.outsideRth = self.outside_rth
        self.ib.placeOrder(self.top_stock, buy_order)
        
    
    def _sell_order(self):
        positions = self.ib.positions()[0].position
        sell_order = MarketOrder("SELL", positions)
        sell_order.outsideRth = self.outside_rth
        self.ib.placeOrder(self.top_stock, sell_order)


    def _check_order(self):
        print("in checking order")
        pass

    def check_RTH(self):
        pre_market_time, post_market_time = self._format_market_times()
        current_time = datetime.now()
        if current_time <= pre_market_time or current_time >= post_market_time:
            return True
        else:
            return False
        
    def _format_market_times(self):
        pre_market_start = str(datetime.strptime('08:30:00', '%H:%M:%S')).split(' ')[1]
        post_market_start = str(datetime.strptime('15:00:00', '%H:%M:%S')).split(' ')[1]        
        pre_market_combined = self.todays_date + " " + pre_market_start
        post_market_combined = self.todays_date + " " + post_market_start
        pre_market_time = datetime.strptime(pre_market_combined, "%Y-%m-%d %H:%M:%S")
        post_market_time = datetime.strptime(post_market_combined, "%Y-%m-%d %H:%M:%S")
        return pre_market_time, post_market_time
