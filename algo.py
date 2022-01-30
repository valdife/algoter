import json
from datetime import datetime
from time import sleep
import numpy
import pandas as pd
import matplotlib.pyplot as plt
from gcapi import GCapiClient  # From https://github.com/rickykim93/gcapi-python

def dema(resp, span):
    EMA1 = resp.ewm(span=span, min_periods=1, adjust=True, ignore_na=False, axis=0).mean()
    EMA2 = EMA1.ewm(span=span, min_periods=1, adjust=True, ignore_na=False, axis=0).mean()
    return 2 * EMA1 - EMA2

# Time data
now = datetime.now()
dt_string = now.strftime("%D-%m-%Y | %H:%M:%S")
print("Data startu programu:", dt_string)

# Accessing an account and fetching account data
print("Uwierzytelnianie...")
with open('account.json', 'r') as read_file:
    account = json.load(read_file)
    api = GCapiClient(
        username=account["username"],
        password=account["password"],
        appkey=account["appkey"],
        proxies=None
    )
    CURRENCY_PAIR = account["currency_pair"]
print("Pomyślnie uwierzytelniono...")
print("Pobieranie informacji o koncie...")
response = api.get_account_info(get=None)
account_id = response['TradingAccounts'][0]['TradingAccountId']
print("Pobieranie informacji o parze walutowej...")
market_id = api.get_market_info(CURRENCY_PAIR, get=None)['Markets'][0]['MarketId']
print("Handluję %s, ID: %s" % (CURRENCY_PAIR, market_id))
START = True
# Trading loop
while START:
    try:
        # Period of trading loop
        sleep(3)
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y | %H:%M:%S")
        print("Start pętli, data:", dt_string)

        # Trading allowed only from Monday to Friday
        if now.weekday() not in range(5):
            print("Dziś nie można handlować, restartuję pętlę.")
            continue

        # Get a specified number of past price points
        response = api.get_prices(market_id=market_id, num_ticks=50)

        # Extract price points from response
        price_data = list(map(lambda p: p['Price'], response['PriceTicks']))
        price_current = price_data[-1]
        # Get ohlc from market
        respOhlc = api.get_ohlc(market_id=market_id,num_ticks=20,interval="DAY",span=1, from_ts=None, to_ts=None).iloc[:,4]

        # Create demas for buy/sell criterias
        price_dema_short = dema(respOhlc, 10).iloc[-1]
        price_dema_long = dema(respOhlc, 20).iloc[-1]

        '''
        plt.plot(dema_long(respOhlc), color='red')
        plt.plot(dema_short(respOhlc), color='black')
        plt.plot(respOhlc,color = 'orange')
        plt.show()
        '''

        print('Ostatnia cena: %s, DEMA(20) = %1.5f , DEMA(10) = %1.5f. Timestamp: %s.' % (
            price_current, price_dema_long, price_dema_short, response['PriceTicks'][-1]))
        # Check our open positions
        response = api.list_open_positions(trading_acc_id=account_id)
        open_positions = response['OpenPositions']
        print('Stan konta: %1.3f' %(cash))
        
        # TODO OPENPOSITIONS CHECK JSON RESPONSE FORMAT AND CORRECT THE CODE
        for openPosition in open_positions:
            openPositionPrice = openPosition['Price']
            print(f'Cena otwartej pozycji: {price_open_position}, current price: {price_data[-1]}')
            if price_dema_short<price_dema_long:
                print('Cena spada, zaczynam sprzedawać...')
                if openPosition['Direction'] == 'sell':
                    response = api.trade_order(
                        1000, price_current,
                        'sell', trading_acc_id=account_id,
                        market_id=market_id, market_name=CURRENCY_PAIR
                    )
                    print('Zlecenie sprzedaży zlożone pomyślnie.')
                    print(response)
                else: continue
            else:
                print('Cena rośnie, zaczynam kupować...')
                if openPosition['Direction'] == 'buy':
                    response = api.trade_order(
                        1000, price_current * 1.001,
                        'buy', trading_acc_id=account_id,
                        market_id=market_id, market_name=CURRENCY_PAIR
                    )
                    print('Próbuję złożyć zlecenie kupna...')
                    if response['Status'] == 2:
                        print('Nie można złożyć zlecenia kupna.')
                    else:
                        print('Zlecenie kupna zlożone pomyślnie.')
                else: continue
        cash = api.get_margin_info(get=None)['Cash']

    except Exception as trader_exception:
        print(trader_exception)