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

        market_data = self.ib.reqMktData(self.top_stock, '', False, False)
        # we can get a lot of different dat from this market data
        # ticks(), vwap(), ticks(), volume(), low52wwk(), high52week(), ask(), modelGreeks, bidGreeks

        self.halted = market_data.halted
        self.price = market_data.marketPrice()
        self.num_shares = self.risk.balance_at_risk // self.price
        

    def execute_trade(self):
        """need functionality for if we bought ORTH and are selling RTH"""
        print(f"\nSignal: {self.signal}")
        if self.halted == 0.0: # not halted

            if not self.ib.positions() and self.signal == 1:
                self._buy_order(self.num_shares)

            elif self.ib.positions() and (self.signal == -1) and (self.risk.trade == None):
                """sell order but we need to check if there is already an order that has not filled then cancel and resubmit"""
                self._sell_order()

            else:
                """this section is to make sure that all positions were sold if not cancel and put in another market order"""
                self._check_order()
        else: # trading halted passing until trading is resumed
            print("----Trading has been Halted----")
    
    def _buy_order(self, num_shares):
        """buys order at market order"""
        if self.risk.trade is not None:
            shares_prev_bought = self.risk.trade.order.filledQuantity
            print(shares_prev_bought)

            #updated_shares = num_shares - shares_prev_bought
            #self.ib.cancelOrder(self.risk.trade.order)
            #self.risk.trade = None
            #buy_order = MarketOrder('BUY', updated_shares)
            #buy_order.outsideRth = self.outside_rth
            #trade = self.ib.placeOrder(self.top_stock, buy_order)
            #self.risk.trade = trade
            # this is where we cancel and rebuy but change the number of shares to what is left
            
        else:
            buy_order = MarketOrder('BUY', num_shares)
            buy_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, buy_order)
            self.risk.trade = trade
            print("----BOUGHT----")
        
    
    def _sell_order(self):
        """sells open positions at market"""
        self.risk.trade = None
        positions = self.ib.positions()[0].position
        sell_order = MarketOrder("SELL", positions)
        sell_order.outsideRth = self.outside_rth
        trade = self.ib.placeOrder(self.top_stock, sell_order)
        self.risk.trade = trade


    def _check_order(self):
        """checks to make sure the orders have been filled, if not then we cancel the orders and place the orders again with updated market"""
        print("----------------in checking order----------------------------")
        if self.risk.trade is not None:
            #print(self.risk.trade)
            if self.risk.trade.orderStatus.status != 'Filled':
                print(f"Order Status: {self.risk.trade.orderStatus.status}")

                if self.risk.trade.order.action == 'BUY':
                    self._buy_order(self.num_shares)
                    print('goin to buy')

                elif self.risk.trade.order.action == 'SELL':
                    self.ib.cancelOrder(self.risk.trade.order)
                    self._sell_order()    

            else:
                self.risk.trade = None
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
