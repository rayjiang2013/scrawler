import argparse
import json
import requests
import time
import smtplib
from email.mime.text import MIMEText
import numpy as np
from datetime import datetime

stock_list = ["AAPL", "AVGO", "BA", "LITE", "LMT", "JPM", "NTES", "PG", "SCHW", "SOGO", "TRVG", "WB"]

def get_outliers(data, m=1):
    u = np.mean(data)
    s = np.std(data)
    filtered = [e for e in data if e > u + m * s]
    return filtered



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
    options = parser.parse_args()
    return options
api_key = "9PXXWXMCD4EE6Z52"
SMTP_SERVER = 'relay.apple.com'

i = 0

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

options = getOptions()
stock_list = options.stock_list
start_time = options.start_time # for example, 2018-02-07 06:30:00
end_time = options.end_time

while True:
    if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > start_time:
        for stock in stock_list:
            time.sleep(1)
            try:
                stock_resp_min = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=%s&interval=1min&apikey=9PXXWXMCD4EE6Z52" % stock)
                stock_data_min = json.loads(stock_resp_min.content)["Time Series (1min)"]
                all_volume = [int(v['5. volume']) for v in sorted(stock_data_min.itervalues(), reverse=True)]
                outliers = get_outliers(all_volume)
                latest_data = stock_data_min[sorted(stock_data_min.iterkeys(), reverse=True)[0]]
                if int(latest_data['5. volume']) in outliers:
                #second_latest_data = stock_data_min[sorted(stock_data_min.iterkeys(), reverse=True)[1]]
                #if latest_data/second_latest_data > 2 or latest_data/second_latest_data < 1/2:
                    send_email("l_jiang@apple.com", "iamabigstone@gmail.com", "high volumn notification for %s" % stock, "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0]))
                    print "Sending email from l_jiang@apple.com to iamabigstone@gmail.com with high volumn notification for " + stock + "Current volume is: %s; time is: %s" % (int(latest_data['5. volume']), sorted(stock_data_min.iterkeys(), reverse=True)[0])
                #print latest_data, second_latest_data
            except Exception:
                print "Exception at https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=%s&interval=1min&apikey=9PXXWXMCD4EE6Z52" % stock
        time.sleep(60)
    if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > end_time:
        break