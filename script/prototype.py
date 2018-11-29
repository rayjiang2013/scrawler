import argparse
import json
import requests
import time
import smtplib
from email.mime.text import MIMEText
import numpy as np
from datetime import datetime

stock_list = ["AAPL", "AVGO", "BA", "LITE", "LMT",
              "JPM", "NTES", "PG", "SCHW", "SOGO", "TRVG", "WB"]
alphavantage_api = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval=1min&apikey=%s&symbol=%s"
iextrading_quote_api = "https://api.iextrading.com/1.0/stock/%s/quote"
iextrading_api = "https://api.iextrading.com/1.0/stock/%s/chart/1d"
#iextrading_api = "https://api.iextrading.com/1.0/stock/%s/chart/date/20181123"
api_key = "9PXXWXMCD4EE6Z52"
SMTP_SERVER = 'relay.apple.com'


def get_outliers(data, m=2):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if e > u + m * s]
    return filtered


def get_outliers_iqr(x, outlier_constant=1.5):
    a = np.array(x)
    upper_quartile = np.percentile(a, 75)
    lower_quartile = np.percentile(a, 25)
    iqr = upper_quartile - lower_quartile
    quartile_set = (lower_quartile - iqr * 1.5, upper_quartile + iqr * 1.5)
    result_list = []
    for y in a.tolist():
        if y > quartile_set[1]:
            result_list.append(y)
    return result_list

# Get options from cli


def getOptions():
    '''
    @summary: To get options from cli
    @return: return namespace of parsed options
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-l",
                        "--stock_list",
                        dest='stock_list',
                        default=stock_list,
                        nargs='+')
    parser.add_argument("-s",
                        "--start_time",
                        dest='start_time',
                        default=argparse.SUPPRESS)
    parser.add_argument("-e",
                        "--end_time",
                        dest='end_time',
                        default=argparse.SUPPRESS)
    parser.add_argument("-a",
                        "--api",
                        dest='api',
                        default="iextrading_api")
    options = parser.parse_args()
    return options


def send_email(sender, to, subject, message):
    # Assemble the email
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    if isinstance(to, list):
        msg['To'] = ', '.join(to)
    else:
        msg['To'] = to

    # Send the email
    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(sender, to, msg.as_string())
    smtp.quit()


def is_low_price(price, history_prices):
    if price < min(history_prices) * 1.001:
        return True


def is_high_price(price, history_prices):
    if price > max(history_prices) * 0.999:
        return True


def alphavantage_main(options):
    stock_list = options.stock_list
    start_time = options.start_time  # for example, 2018-02-07 06:30:00
    end_time = options.end_time
    #start_time = "2018-11-20 06:40:00"
    while True:
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > start_time:
            for stock in stock_list:
                # 1 sec seems to be enough to get consistent response from this
                # api
                time.sleep(1)
                try:
                    stock_resp_min = requests.get(
                        alphavantage_api % (api_key, stock))
                    stock_data_min = json.loads(stock_resp_min.content)[
                        "Time Series (1min)"]
                    all_volume = [int(v['5. volume']) for v in sorted(
                        stock_data_min.itervalues(), reverse=True)]
                    all_values = [float(v['4. close']) for v in sorted(
                        stock_data_min.itervalues(), reverse=True)]
                    #outliers = get_outliers(all_volume)
                    outliers = get_outliers_iqr(all_volume)
                    latest_data = stock_data_min[sorted(
                        stock_data_min.iterkeys(), reverse=True)[0]]
                    if int(latest_data['5. volume']) in outliers:
                        #second_latest_data = stock_data_min[sorted(stock_data_min.iterkeys(), reverse=True)[1]]
                        # if latest_data/second_latest_data > 2 or latest_data/second_latest_data < 1/2:
                        #send_email("l_jiang@apple.com", "iamabigstone@gmail.com", "high volumn notification for %s" % stock, "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0]))
                        # print "Sending email from l_jiang@apple.com to
                        # iamabigstone@gmail.com with high volumn notification
                        # for " + stock + "Current volume is: %s; time is: %s"
                        # % (int(latest_data['5. volume']),
                        # sorted(stock_data_min.iterkeys(), reverse=True)[0])
                        requests.post('http://perfreporting.apple.com:9090/text', {
                            'number': '3522223838',
                            'message': "High volumn notification for %s. Current volume is: %s; time is: %s" % (stock, int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0])
                        })
                        print "Sending message to 3522223838 with high volumn notification for " + stock + "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0])
                        if is_low_price(float(latest_data["4. close"]), all_values):
                            requests.post('http://perfreporting.apple.com:9090/text', {
                                'number': '3522223838',
                                'message': "Low price notification for %s. Current price is: %s; time is: %s" % (stock, latest_data['4. close'], sorted(stock_data_min.iterkeys(), reverse=True)[0])
                            })
                            print "Sending message to 3522223838 with low price notification for " + stock + "Current volume is: %s; time is: %s" % (latest_data['4. close'], sorted(stock_data_min.iterkeys(), reverse=True)[0])
                        elif is_high_price(float(latest_data["4. close"]), all_values):
                            requests.post('http://perfreporting.apple.com:9090/text', {
                                'number': '3522223838',
                                'message': "High price notification for %s. Current price is: %s; time is: %s" % (stock, latest_data['4. close'], sorted(stock_data_min.iterkeys(), reverse=True)[0])
                            })
                            print "Sending message to 3522223838 with high price notification for " + stock + "Current volume is: %s; time is: %s" % (latest_data['4. close'], sorted(stock_data_min.iterkeys(), reverse=True)[0])

                    # print latest_data, second_latest_data
                except Exception, e:
                    print e
                    print "Exception at " + alphavantage_api % (api_key, stock) + " at %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(59)
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time:
            break


def iextrading_main(options):
    stock_list = options.stock_list
    start_time = options.start_time  # for example, 2018-02-07 06:30:00
    end_time = options.end_time
    #start_time = "2018-11-20 06:40:00"
    while True:
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > start_time:
            for stock in stock_list:
                time.sleep(1)
                try:
                    stock_resp_min = requests.get(iextrading_api % (stock))
                    stock_data_min = json.loads(stock_resp_min.content)
                    all_volume = [int(v.get('marketVolume', 0))
                                  for v in stock_data_min]
                    # volume_exclude_zero = [v for v in all_volume[] if v!= 0]
                    if len(all_volume) <= 100:
                        volume_to_check = all_volume
                    else:
                        volume_to_check = all_volume[-100:]
                    #outliers = get_outliers(all_volume)
                    outliers = get_outliers_iqr(volume_to_check)
                    print "time: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print "outliers: %s" % outliers
                    latest_data = sorted(
                        stock_data_min, key=lambda s: s['minute'], reverse=True)[0]
                    print "latest_data: %s" % latest_data
                    if int(latest_data['marketVolume']) in outliers:
                        #second_latest_data = stock_data_min[sorted(stock_data_min.iterkeys(), reverse=True)[1]]
                        # if latest_data/second_latest_data > 2 or latest_data/second_latest_data < 1/2:
                        #send_email("l_jiang@apple.com", "iamabigstone@gmail.com", "high volumn notification for %s" % stock, "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0]))
                        # print "Sending email from l_jiang@apple.com to
                        # iamabigstone@gmail.com with high volumn notification
                        # for " + stock + "Current volume is: %s; time is: %s"
                        # % (int(latest_data['5. volume']),
                        # sorted(stock_data_min.iterkeys(), reverse=True)[0])
                        requests.post('http://perfreporting.apple.com:9090/text', {
                            'number': '3522223838',
                            'message': "High volumn notification for %s. Current volume is: %s; time is: %s" % (stock, int(latest_data['marketVolume']), latest_data['minute'])
                        })
                        print "Sending message to 3522223838 with high volumn notification for " + stock + "Current volume is: %s; time is: %s" % (int(latest_data['marketVolume']), latest_data['minute'])
                    # print latest_data, second_latest_data
                except Exception, e:
                    print e
                    print "Exception at " + iextrading_api % (stock) + " at %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(59)
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time:
            break


def iextrading_quote_main(options):
    stock_list = options.stock_list
    start_time = options.start_time  # for example, 2018-02-07 06:30:00
    end_time = options.end_time
    #start_time = "2018-11-20 06:40:00"
    from collections import defaultdict
    total_volumes = defaultdict(list)
    volumes = defaultdict(list)
    prices = defaultdict(list)
    while True:
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time.split()[0] + ' 05:00:00':
            for stock in stock_list:
                time.sleep(1)
                try:
                    stock_resp_min = requests.get(
                        iextrading_quote_api % (stock))
                    stock_data_min = json.loads(stock_resp_min.content)
                    total_volume = int(stock_data_min.get('latestVolume', 0)
                                       ) if stock_data_min.get('latestVolume') is not None else 0
                    total_volumes[stock].append(total_volume)
                    if len(total_volumes[stock]) > 1:
                        volume = total_volumes[stock][-1] - \
                            total_volumes[stock][-2]
                    else:
                        volume = 0
                    # only check outlier from non zero volumes
                    if volume > 0:
                        volumes[stock].append(volume)
                    price = stock_data_min['extendedPrice']
                    prices[stock].append(price)
                    if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > start_time:
                        # volume_exclude_zero = [v for v in all_volume[] if v!=
                        # 0]
                        if len(volumes[stock]) <= 100:
                            volume_to_check = volumes[stock]
                        else:
                            volume_to_check = volumes[stock][-100:]
                        #outliers = get_outliers(all_volume)
                        outliers = get_outliers_iqr(volume_to_check)
                        print "time: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print "outliers: %s" % outliers
                        print "latest_data: %s" % stock_data_min
                        print "volumes: %s" % volumes
                        print "total_volumes: %s" % total_volumes
                        print "prices: %s" % prices
                        if volumes[stock][-1] in outliers:
                            #second_latest_data = stock_data_min[sorted(stock_data_min.iterkeys(), reverse=True)[1]]
                            # if latest_data/second_latest_data > 2 or latest_data/second_latest_data < 1/2:
                            #send_email("l_jiang@apple.com", "iamabigstone@gmail.com", "high volumn notification for %s" % stock, "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0]))
                            # print "Sending email from l_jiang@apple.com to
                            # iamabigstone@gmail.com with high volumn notification
                            # for " + stock + "Current volume is: %s; time is: %s"
                            # % (int(latest_data['5. volume']),
                            # sorted(stock_data_min.iterkeys(),
                            # reverse=True)[0])
                            extended_price_time = datetime.fromtimestamp(
                                stock_data_min["extendedPriceTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                            high_volume_message = "High volumn notification for %s. Current volume is: %s"\
                                "; time is: %s" % (
                                    stock, volume, extended_price_time)
                            requests.post('http://perfreporting.apple.com:9090/text', {
                                'number': '3522223838',
                                'message': high_volume_message
                            })
                            print high_volume_message
                            if is_low_price(price, prices[stock]):
                                low_price_message = "Low price notification for %s. Current price is: %s; time is: %s" % (
                                    stock, price, extended_price_time)
                                requests.post('http://perfreporting.apple.com:9090/text', {
                                    'number': '3522223838',
                                    'message': low_price_message
                                })
                                print low_price_message
                            elif is_high_price(price, prices[stock]):
                                high_price_message = "High price notification for %s. Current price is: %s; time is: %s" % (
                                    stock, price, extended_price_time)
                                requests.post('http://perfreporting.apple.com:9090/text', {
                                    'number': '3522223838',
                                    'message': high_price_message
                                })
                                print high_price_message

                        # print latest_data, second_latest_data
                except Exception, e:
                    print e
                    print "Exception at " + iextrading_api % (stock) + " at %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(59)
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time:
            break
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time.split()[0] + ' 14:00:00':
            break


if __name__ == '__main__':
    options = getOptions()
    api = options.api
    if api == "alphavantage_api":
        alphavantage_main(options)
    elif api == "iextrading_api":
        iextrading_main(options)
    elif api == "iextrading_quote_api":
        iextrading_quote_main(options)
    else:
        print "unrecognized api!! please check your -a option"
