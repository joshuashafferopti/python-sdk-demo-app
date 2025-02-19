# Python SDK Demo App
# Copyright 2016 Optimizely. Licensed under the Apache License
# View the documentation: http://optimize.ly/py-sdk 
from __future__ import print_function

import csv
import json
import os
from operator import itemgetter

# from optimizely_config_manager import OptimizelyConfigManager

'''2020 updates:
- updated the SDK version to the latest in requirements.txt
- deleted optimizely_config_manager.py + its references (get_obj)
- renamed project_ID to SDK_KEY, renamed config_manager to optimizely_client to better reflect the current SDK
'''
from optimizely import optimizely
from optimizely.config_manager import PollingConfigManager
from optimizely import logger
import logging

SDK_KEY = 'Lsmf9dMjernYf1TMcF4Bq'

CONF_MANAGER = PollingConfigManager(
    sdk_key=SDK_KEY,
    update_interval=10
)

from flask import Flask, render_template, request

application = Flask(__name__, static_folder='images')
application.secret_key = os.urandom(24)

optimizely_client = optimizely.Optimizely(config_manager=CONF_MANAGER,
                                          logger=logger.SimpleLogger(min_level=logging.INFO))


# optimizely_client = optimizely.Optimizely(datafile, logger=logger.SimpleLogger(min_level=logging.INFO))

def build_items():
    items = []
    reader = csv.reader(open('items.csv', 'r'))
    for line in reader:
        items.append({'name': line[0],
                      'color': line[1],
                      'category': line[2],
                      'price': int(line[3][1:]),
                      'imageUrl': line[4]})
    return items


# render homepage
@application.route('/')
def index():
    items = build_items()
    return render_template('index.html', data=items)


# display items
@application.route('/shop', methods=['GET', 'POST'])
def shop():
    user_id = request.form['user_id']

    # compute variation_key
    variation_key = optimizely_client.activate('ab_test_1', user_id)

    # load items
    sorted_items = build_items()

    # sort by price
    if variation_key == 'price':
        print("In variation 1")
        sorted_items = sorted(sorted_items, key=itemgetter('price'))

    # sort by category
    if variation_key == 'category':
        print("In variation 2")
        sorted_items = sorted(sorted_items, key=itemgetter('category'))

    return render_template('index.html',
                           data=sorted_items, user_id=user_id, variation_key=variation_key)


# process a purchase event
@application.route('/buy', methods=['GET', 'POST'])
def buy():
    user_id = request.form['user_id']

    # track conversion event
    optimizely_client.track("click_buy", user_id)

    return render_template('purchase.html')


# webhook logic
@application.route('/webhook', methods=['POST'])
def webhook_event():
    data = request.get_json()

    event_type = data['event']
    # use CDN URL from webhook payload
    if event_type == 'project.datafile_updated':
        url = data['data']['cdn_url']
        optimizely_client.set_obj(url)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}


if __name__ == '__main__':
    application.debug = True
    application.run(port=4001)
