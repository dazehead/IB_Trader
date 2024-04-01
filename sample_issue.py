from ib_insync import *
util.patchAsyncio()

"""connecting to IB"""
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

counter = 0 # this is used to let program run for little longer
contracts = [] # stores stock objects

"""this is the scanner to search for tickers"""
gainSub = ScannerSubscription(
    instrument="STK",
    locationCode="STK.US.MAJOR",
    scanCode='TOP_PERC_GAIN',
    stockTypeFilter="CORP")

tagValues = [TagValue("priceAbove", '1'),
                TagValue("priceBelow", '20'),
                TagValue("volumeAbove", '999999'),
                TagValue("changePercAbove", '100')]

scanDataList = ib.reqScannerSubscription(gainSub, [], tagValues)
ib.sleep(1)
        
"""retrieves all the tickers-converts to Stock object and appends them to a list"""
for data in scanDataList:
    stock = Stock(data.contractDetails.contract.symbol, 'SMART', 'USD')
    ib.qualifyContracts(stock)
    contracts.append(stock)
print(f'\n{len(scanDataList)} Tickers found.')
print(f"here are the contracts the scanner has picked up:\n{[contract.symbol for contract in contracts]}")


"""The logic below will ask us to remove 1 of the tickers so that later we can simulate the scanner getting a new ticker"""
for i ,contract in enumerate(contracts):
    symbol = contract.symbol
    print(f'{i+1}. {symbol}')
if len(contracts) > 1:
    choice = input('Please remove 1 of these tickers(1 or 2)?\n').lower()
    while len(contracts) > 1:
        to_be_removed = int(choice) - 1
        rejected_ticker = contracts.pop(to_be_removed)
        for i, contract in enumerate(contracts):
            symbol = contract.symbol
            print(f'\n{i+1}. {symbol}')
        print(f"Here are the contracts after we have removed one: \n{[contract.symbol for contract in contracts]}")
        choice = input(f'{rejected_ticker.symbol} will be added after 3 iterations or greater. please enter y to continue?\n').lower()


"""getting market data storing the data in a dicionary ex: {'AAPL': barData}"""
live_bars_dict = {}
barsize = '10 secs'
for contract in contracts:
    live_bars_dict[contract.symbol] = ib.reqHistoricalData(
        contract = contract,
        endDateTime= '',
        durationStr= '1 D',
        barSizeSetting= barsize,
        whatToShow = 'TRADES',
        useRTH= False,
        keepUpToDate= True)
    ib.sleep(1)


last_update_time = live_bars_dict[contracts[0].symbol][-1].date
def hasNewBarForAllSymbols(live_bars_dict):
    """returns True if all symbols have recieved a new bar"""
    global last_update_time
    latest_timestamps = [bars[-1].date for symbol,bars in live_bars_dict.items()]
    # Check if all latest timstamps are equal
    new_bar_for_all_symbols = all(time==latest_timestamps[0] for time in latest_timestamps)
    if new_bar_for_all_symbols: # if all latest timestamps are equal
        if latest_timestamps[0] > last_update_time: # means we have a new bar
            last_update_time = latest_timestamps[0]
        else:
            new_bar_for_all_symbols = False
    return new_bar_for_all_symbols


def on_bar_update(bars, hasNewBar):
    global contracts
    global live_bars_dict
    global counter
    if hasNewBarForAllSymbols(live_bars_dict):
        """if all historical_data has a new symbol we start strategy here we just increse the counter"""
        counter += 1            
        print(f'\n-------counter: {counter}-------')
        print(f'current live_bars_dict: {live_bars_dict.keys()}')


def onScanData(scanDataList):
    global live_bars_dict
    global contracts
    global counter
    current_tickers = [contract.symbol for contract in contracts]
    if counter < 3:
        pass
    else:
        for data in scanDataList:
            """Checks if we have new tickers"""
            new_ticker = data.contractDetails.contract.symbol
            if new_ticker not in current_tickers:
                print(f'\n-------New Ticker {new_ticker}-------')
                stock = Stock(new_ticker, 'SMART', 'USD')
                contracts.append(stock)
                print(f'contracts: {[contract.symbol for contract in contracts]}')

                # This is where I get error raise RuntimeError('This event loop is already running)
                live_bars_dict[new_ticker] = ib.reqHistoricalData(
                    contract = stock,
                    endDateTime= '',
                    durationStr= '1 D',
                    barSizeSetting= barsize,
                    whatToShow = 'TRADES',
                    useRTH= False,
                    keepUpToDate= True)
                print('This will print if its successful')


try:
    scanDataList.updateEvent.clear()
    scanDataList.updateEvent += onScanData
    ib.barUpdateEvent.clear()
    ib.barUpdateEvent+= on_bar_update
    ib.sleep(10000)
except KeyboardInterrupt:
    print('exitted program')