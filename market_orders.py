import time
from ib_insync import *

class Trade:
    def __init__(self, ib, risk, signals, contract, counter=None):
        self.ib = ib
        self.risk = risk
        self.top_stock = contract
        self.pre_market_time = time(8,30,0)
        self.post_market_time = time(3,30,0)
        self.outside_rth = self.check_RTH
        if not counter:
            self.signal = signals[counter]
        else:
            self.signal = signals[-1]


    def execute_trade(self, close):
        """need functionality for if we bought ORTH and are selling RTH"""
        # maybe this is the point to check logs for what time the order was executed and what type
        num_shares = self.risk.calculate_shares(close)
        if self.outside_rth:
            if not self.ib.positions() and self.signal == 1:
                buy_order = MarketOrder('BUY', num_shares)
                trade = self.ib.placeOrder(self.top_stock, buy_order)
                while not trade.isDone():
                    self.ib.waitOnUpdate()
                print("BOUGHT")
            elif self.signal == -1 and self.ib.positions():
                positions = self.ib.positions()[0].position
                sell_order = MarketOrder('SELL', positions)
                trade = self.ib.placeOrder(self.top_stock, sell_order)
                while not trade.isDone():
                    self.ib.waitOnUpdate()
                print("SOLD")
            else:
                pass
        else:
            if not self.ib.positions() and self.signal == 1:
                buy_order = MarketOrder('BUY', num_shares)
                trade = self.ib.placeOrder(self.top_stock, buy_order)
                while not trade.isDone():
                    self.ib.waitOnUpdate()
                print("BOUGHT")
            elif self.signal == -1 and self.ib.positions():
                positions = self.ib.positions()[0].position
                sell_order = MarketOrder('SELL', positions)
                trade = self.ib.placeOrder(self.top_stock, sell_order)
                while not trade.isDone():
                    self.ib.waitOnUpdate()
                print("SOLD")
            else:
                self._update_stop_loss()

    def _update_stop_loss(self):
        pass

    def check_RTH(self):
        current_time = time.localtime()
        #print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S', current_time)}")
        formatted_time = time.strftime('%H:%M:%S', current_time)
        if formatted_time <= self.pre_market_time and formatted_time >= self.post_market_time:
            print("outside trading hours")
            return True
        else:
            print("inside trading hours")
            return False