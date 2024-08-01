from function import *
import twstock
import pandas as pd
import warnings
from tqdm import tqdm
import yfinance as yf


if __name__ == '__main__':

    warnings.filterwarnings("ignore")

    sell_info = to_sell('2812', '2024-04-01', '2024-07-10', 19.1)
    print(sell_info)
    sell_info = to_sell('6257', '2024-04-01', '2024-07-11', 81.9)
    print(sell_info)
    sell_info = to_sell('2342', '2024-04-01', '2024-07-19', 33.5)
    print(sell_info)
    sell_info = to_sell('006208', '2024-04-01', '2024-08-01', 106.8)
    print(sell_info)
    sell_info = to_sell('1440', '2024-04-01', '2024-07-31', 17.7)
    print(sell_info)
    sell_info = to_sell('9934', '2024-04-01', '2024-07-31', 18.55)
    print(sell_info)
    sell_info = to_sell('0056', '2024-04-01', '2024-07-26', 38.67)
    print(sell_info)

    df = Parse_all_category_stocks()
    category = ['all']
    update_from_offline = True
    update_from_online = True
    stock_list = Update_potential_stock(
        update_from_offline, update_from_online, category)

    to_buy_main(stock_list, '2024-04-01')

    # link = df[df['Category'] == '半導體業']['link'].values
    # links = df['link'].values
    # stock_list = []
    # for link in links:
    #     stocks = Parse_certain_category_stocks(link)
    #     stock_list.extend(stocks)

    # plot and analysis
    # figure_plot('3533', 2023, 1)
