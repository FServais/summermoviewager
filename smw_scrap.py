# -*- coding: utf-8 -*-

import argparse
import requests
import re
import json
import time
import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Print iterations progress
# def print_progress (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
#     """
#     Call in a loop to create terminal progress bar
#     @params:
#         iteration   - Required  : current iteration (Int)
#         total       - Required  : total iterations (Int)
#         prefix      - Optional  : prefix string (Str)
#         suffix      - Optional  : suffix string (Str)
#         decimals    - Optional  : positive number of decimals in percent complete (Int)
#         length      - Optional  : character length of bar (Int)
#         fill        - Optional  : bar fill character (Str)
#     """
#     percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
#     filledLength = int(length * iteration // total)
#     bar = fill * filledLength + '-' * (length - filledLength)
#     print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
#     # Print New Line on Complete
#     if iteration == total:
#         print()

# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

class SMWPage:
    def __init__(self, year):
        self._URL = 'http://smoview.a2hosted.com/index.php'
        self.year = year

    def _get_url(self):
        return '{}?year={}'.format(self._URL, self.year)

    def parse(self):
        from bs4 import BeautifulSoup

        result = []

        rsp = None
        try:
            rsp = requests.get(self._get_url(), verify=False)
        except Exception as e:
            print('Exception when retrieving the page {}'.format(self._url))
            print('{}'.format(e))
            return

        soup = BeautifulSoup(rsp.text, 'html.parser')

        scoreboardpanel = soup.findAll("table", {"class": ["scoreboardpanel"]})

        for panel in scoreboardpanel:
            rows = panel.findAll("tr", {"class": ["mw"]})

            for row in rows:
                name = row.findAll("td", {"class": ["name"]})[0].next
                revenue = row.findAll("td", {"class": ["result"]})[0].next
                matchObj_revenue = re.search(r'([0-9]+)', revenue)

                position_in_year = row.findAll("td", {"class": ["pos"]})[0].next
                matchObj_pos = re.search(r'([0-9]{1,2})', position_in_year)

                result.append({
                    'name': name,
                    'revenue': int(matchObj_revenue.group(1)),
                    'position_in_year': int(matchObj_pos.group(1)),
                    'year': self.year
                })

        return result


if __name__ == '__main__':
    years = range(2007, 2017+1)

    result = []

    for year in years:
        page = SMWPage(year)
        result += page.parse()

    print(result)
