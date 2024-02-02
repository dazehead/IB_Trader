from datetime import datetime
from ib_insync import *

class Trade:
    """A class to handle interactions with IB"""
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
        self.ask = market_data.ask
        self.bid = market_data.bid
        #self.midpoint = market_data.midpoint
        

    def execute_trade(self):
        """Logic for when to buy and sell based off signals and if we already hold positions"""
        print(f"Signal: {self.signal}")
        print(f"Spread: {self.bid}-{self.ask}")
        if self.halted == 0.0: # not halted

            if not self.ib.positions() and self.signal == 1 and self.risk.trade is None:
                self._buy_order(self.num_shares)

            elif self.ib.positions() and (self.signal == -1) and (self.risk.trade is None):
                """sell order but we need to check if there is already an order that has not filled then cancel and resubmit"""
                self._sell_order()

            else:
                """this section is to make sure that all positions were sold if not cancel and put in another market order"""
                self._check_order()
        else: # trading halted passing until trading is resumed
            print("----Trading has been Halted----")
    
    def _buy_order(self, num_shares):
        """Buys order at market order"""
        if self.outside_rth:
            self.risk.trade_num_shares = num_shares
            buy_order = LimitOrder('BUY', num_shares, self.ask)
            buy_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, buy_order)
            self.risk.trade = trade
            print("----BOUGHT----")
        else:
            self.risk.trade_num_shares = num_shares
            buy_order = MarketOrder('BUY', num_shares)
            buy_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, buy_order)
            self.risk.trade = trade
            print("----BOUGHT----")
        
    
    def _sell_order(self):
        if self.outside_rth:
            print("outside RTH")
            """Sells open positions at market"""
            self.risk.trade = None
            positions = self.ib.positions()[0].position
            sell_order = LimitOrder("SELL", positions, self.ask)
            sell_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, sell_order)
            self.risk.trade = trade
        else:
            """Sells open positions at market"""
            self.risk.trade = None
            positions = self.ib.positions()[0].position
            sell_order = MarketOrder("SELL", positions)
            sell_order.outsideRth = self.outside_rth
            trade = self.ib.placeOrder(self.top_stock, sell_order)
            self.risk.trade = trade


    def _check_order(self):
        """Checks to make sure the orders have been filled, if not then we cancel the orders and place the orders again with updated market"""
        print("----------------in checking order----------------------------\n")
        if self.risk.trade is not None:
            #print(self.risk.trade)
            if self.risk.trade.orderStatus.status != 'Filled' and self.risk.trade.orderStatus.status != 'Cancelled':
                print(f"Order Status: {self.risk.trade.orderStatus.status}")             

                if self.risk.trade.order.action == 'BUY':
                    if self.risk.trade_counter == 3:
                        self.risk.trade_counter = 0
                        shares_prev_bought = self.risk.trade.order.totalQuantity
                        self.num_shares = round(self.risk.trade_num_shares - shares_prev_bought, 1)
                        #print(f"filled: {shares_prev_bought} : needing: {self.num_shares}")
                        self.ib.cancelOrder(self.risk.trade.order)
                        self._buy_order(self.num_shares)
                        print('canceling and re-buying with calculated shares')
                    elif self.risk.trade.orderStatus.status == 'PreSubmitted':
                        self.risk.trade_counter += 1
                    elif self.risk.tradeorderStatus.status == 'Submitted':
                        self.risk.trade_counter += 1
 

                elif self.risk.trade.order.action == 'SELL':
                    self.ib.cancelOrder(self.risk.trade.order)
                    self._sell_order()    

            else:
                self.risk.trade = None
        pass

    def check_RTH(self):
        """returns whether it is oRTH or not"""
        pre_market_time, post_market_time = self._format_market_times()
        current_time = datetime.now()
        if current_time <= pre_market_time or current_time >= post_market_time:
            return True
        else:
            return False
        
    def _format_market_times(self):
        """Helper function to format datetimes of pre/post market"""
        pre_market_start = str(datetime.strptime('08:30:00', '%H:%M:%S')).split(' ')[1]
        post_market_start = str(datetime.strptime('15:00:00', '%H:%M:%S')).split(' ')[1]        
        pre_market_combined = self.todays_date + " " + pre_market_start
        post_market_combined = self.todays_date + " " + post_market_start
        pre_market_time = datetime.strptime(pre_market_combined, "%Y-%m-%d %H:%M:%S")
        post_market_time = datetime.strptime(post_market_combined, "%Y-%m-%d %H:%M:%S")
        return pre_market_time, post_market_time
