import time
from datetime import datetime, timedelta
from ib_insync import *

class Trade:
    def __init__(self, ib, risk, signals, contract, counter=None):
        self.ib = ib
        self.risk = risk
        self.top_stock = contract

        self.todays_date = str(datetime.now()).split(' ')[0]
        pre_market_start = str(datetime.strptime('08:30:00', '%H:%M:%S')).split(' ')[1]
        post_market_start = str(datetime.strptime('15:00:00', '%H:%M:%S')).split(' ')[1]        
        pre_market_combined = self.todays_date + " " + pre_market_start
        post_market_combined = self.todays_date + " " + post_market_start
        self.pre_market_time = datetime.strptime(pre_market_combined, "%Y-%m-%d %H:%M:%S")
        self.post_market_time = datetime.strptime(post_market_combined, "%Y-%m-%d %H:%M:%S")

        #self.post_market_time = datetime.strptime('15:00:00', '%H:%M:%S')
        self.outside_rth = self.check_RTH()


        self.trade = None
        if counter is not None:
            self.signal = signals[counter]
        else:
            self.signal = signals[-1]


    def execute_trade(self):
        """need functionality for if we bought ORTH and are selling RTH"""
        # maybe this is the point to check logs for what time the order was executed and what type
        price = self.ib.reqMktData(self.top_stock,'', False, False).marketPrice()
        num_shares = self.risk.balance_at_risk // price

        if not self.ib.positions() and self.signal == 1:
            self._buy_order(num_shares)
        elif self.ib.positions() and (self.signal == -1):
            self._sell_order()
        else:
            self._check_order()
    
    def _buy_order(self, num_shares):
        buy_order = MarketOrder('BUY', num_shares, outside_rth=self.outside_rth)
        self.trade = self.ib.placeOrder(self.top_stock, buy_order)
        print(self.trade.orderStatus)
    
    def _sell_order(self):
        positions = self.ib.positions()[0].position
        sell_order = MarketOrder("SELL", positions, outside_rth=self.outside_rth)
        self.trade = self.ib.placeOrder(self.stop_stock, sell_order)
        print(self.trade.orderStatus)
        self.trade = None


    def _check_order(self):
        print("in checking order")
        pass

    def check_RTH(self):
        current_time = datetime.now()
        print(self.pre_market_time)
        if current_time <= self.pre_market_time or current_time >= self.post_market_time:
            return True
        else:
            return False