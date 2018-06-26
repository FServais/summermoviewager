# coding=utf-8
import argparse
import csv

import re
import requests
import json

import pandas as pd
import numpy as np

# Print iterations progress
import sys


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
    bar = '=' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

class OMDB():
    def __init__(self, apikey):
        self.apikey = apikey

    def _init_params(self):
        return {
            'apikey': self.apikey
        }

    def url(self):
        return 'http://www.omdbapi.com/'

    def _process_response(self, json_rsp):
        headers_to_skip = ['Poster', 'Awards', 'Response', 'DVD', 'Released', 'imdbVotes', 'Website', 'Language']
        headers = []

        result = {}

        if 'Error' in json_rsp.keys():
            # print('Error: {}'.format(json_rsp['Error']))
            return

        for k, v in json_rsp.iteritems():
            if k == 'Ratings':
                if 'Internet Movie Database' in json_rsp[k]:
                    result['IMD_score'] = json_rsp[k]['Internet Movie Database']
                else:
                    result['IMD_score'] = 'N/A'

                if 'Rotten Tomatoes' in json_rsp[k]:
                    result['RT_score'] = json_rsp[k]['Rotten Tomatoes']
                else:
                    result['RT_score'] = 'N/A'

                if 'Metacritic' in json_rsp[k]:
                    result['MC_score'] = json_rsp[k]['Metacritic']
                else:
                    result['MC_score'] = 'N/A'

                headers.append('IMD_score')
                headers.append('RT_score')
                headers.append('MC_score')

            elif k in headers_to_skip:
                continue

            elif k == 'Writer':
                writers = self._process_writers(v.encode('utf-8'))
                for w in writers:
                    name, profession = w
                    if profession:
                        header = '{}_{}'.format('_'.join(name.split(' ')), '_'.join(profession.split(' ')))
                    else:
                        header = '{}'.format('_'.join(name.split(' ')))
                    headers.append(header)

                    result[header] = 1

            elif k == 'Actors':
                actors = self._process_actors(v)
                for act in actors:
                    header = '{}_actor'.format('_'.join(act.split(' ')).encode('utf-8'))
                    headers.append(header)

                    result[header] = 1

            elif k == 'Genre':
                genres = self._process_genre(v)
                for g in genres:
                    header = '{}_genre'.format('_'.join(g.split(' ')))
                    headers.append(header)

                    result[header] = 1

            elif k == 'BoxOffice':
                box_office = self._process_box_office(v)
                result['BoxOffice'] = box_office

                headers.append('BoxOffice')

            elif k == 'Runtime':
                runtime = self._process_runtime(v)

            else:
                result[k] = v
                headers.append(k)

        return result

    def _process_writers(self, str_writer):
        regex = r'([a-zA-Z-\. ]+)(?:\(([a-zA-Z ]+)\))?'
        writers = str_writer.split(', ')

        result = []

        for w in writers:
            res = re.match(regex, w)
            if not res:
                print('No match for {}'.format(w))
            elif res.group(2):
                result.append((res.group(1), res.group(2)))
            else:
                result.append((res.group(1), None))

        return result

    def _process_actors(self, str_actors):
        return self._process_list_comma_separated(str_actors)

    def _process_genre(self, str_actors):
        return self._process_list_comma_separated(str_actors)

    def _process_list_comma_separated(self, _str):
        return _str.split(', ')

    def _process_box_office(self, _str):
        if _str == 'N/A':
            return _str
        return int(int(_str.replace(',', '').replace('$', ''))/1000000)

    def _process_runtime(self, _str):
        if _str.endswith(' min'):
            return _str[:-4]

        return 'N/A'

    def search(self, title, year=None):
        params = self._init_params()
        params['t'] = title
        if year:
            params['y'] = year

        return self._send_search(params)

    def search_imdb_id(self, id):
        params = self._init_params()
        params['i'] = id

        return self._send_search(params)

    def _send_search(self, params):
        rsp = requests.get(self.url(), params=params)
        if rsp.status_code > 299:
            print('ERROR - Request to {} with params {} failed'.format(self.url(), params))
            return

        return self._process_response(json.loads(rsp.text))

def get_args():
    arg_parser = argparse.ArgumentParser('Queries IMDB (via OMDB) from movie names for movie information.')
    arg_parser.add_argument('-a', '--apikey', action='store', required=True)
    arg_parser.add_argument('-m', '--movies', action='store', required=True)
    arg_parser.add_argument('-o', '--output', action='store', required=True)

    return arg_parser.parse_args()

def get_fixed_mapping():
    return {
        'The Karate Kid': 'tt1155076',
        'Ghostbusters (2016)': 'tt1289401'
    }

if __name__ == '__main__':
    args = get_args()
    apikey = args.apikey
    movies_file = args.movies
    output = args.output

    omdb = OMDB(apikey)
    # res = omdb.search('Spider-Man 3')

    smw_movies = pd.read_csv(movies_file, delimiter=';', encoding="utf8")

    iteration = 1
    errors = []
    results = []

    mapping = get_fixed_mapping()

    for m in smw_movies['name']:
        print_progress(iteration, len(smw_movies['name']), suffix=m.encode('utf-8'))

        res = None

        if m in mapping:
            res = omdb.search_imdb_id(mapping[m])

        else:
            res = omdb.search(m)

        if not res:
            errors.append(m)

        results.append(res)

        iteration += 1

    df = pd.DataFrame(results)
    df.to_csv(output, sep=';', encoding="utf-8")

    if errors:
        print(errors)