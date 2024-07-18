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
    sell_info = to_sell('2342', '2024-04-01', '2024-07-12', 34.15)
    print(sell_info)

    # df = Parse_all_category_stocks()
    stock_list = Update_potential_stock()
    #
    # link = df[df['Category'] == '半導體業']['link'].values
    # links = df['link'].values
    # stock_list = []
    # for link in links:
    #     stocks = Parse_certain_category_stocks(link)
    #     stock_list.extend(stocks)
    stock_list = list(set(stock_list))  # remove duplicate items
    to_buy_main(stock_list, '2024-04-01')

    # plot and analysis
    # figure_plot('3533', 2023, 1)
