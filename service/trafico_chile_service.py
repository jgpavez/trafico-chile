# -*- coding: utf-8 -*-

# Servicio de monitoreo de tweets que mencionan a trafico_chile
# actualizado cada 1 minuto.

import sys
import twitter
import couchdb
import locale
import time
import logging
from datetime import date
from couchdb.design import ViewDefinition
from twitter__util import makeTwitterRequest

SEARCH_TERM = '@trafico_chile'
MAX_PAGES = 15
LOGGER_OUT = '../log/service.log'
SLEEP_TIME = 60

KW = {
    'domain' : 'search.twitter.com',
    'count' : 200,
    'rpp' : 100,
    'q' : SEARCH_TERM,
}
server = couchdb.Server('http://localhost:5984')
DB = 'trafico_chile'

try:
    db = server.create(DB)
except couchdb.http.PreconditionFailed, e:
    db = server[DB]

t = twitter.Twitter(domain = 'search.twitter.com')

# Setting logger
logger = logging.getLogger('trafico_chile_service')
fl = logging.FileHandler(LOGGER_OUT)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fl.setFormatter(formatter)
logger.addHandler(fl)
logger.setLevel(logging.DEBUG)

print 'Starting fetching Service, you can stop it with ctrl-c'
while 1:
    actual_time = time.localtime(time.time())
    print 'Starting fetch of tweets at %d-%d-%d : %d:%d' % (actual_time[0],actual_time[1],actual_time[2],actual_time[3],actual_time[4])
    total_fetched = 0
    tweets_with_ids = []
    for page in range(1,16):    
        KW['page'] = page
        tweets = makeTwitterRequest(t, t.search, **KW)
        for tweet in tweets['results']:
            tweet['_id'] = tweet['id_str']
        db.update(tweets['results'], all_or_nothing = True)
        print 'Fetched %i tweets' % len(tweets['results'])
        total_fetched += len(tweets['results'])
    print 'Fetched %d tweets, now waiting 1 minute' % total_fetched
    logger.info('Fetched %d tweets, no problem' % total_fetched)
    time.sleep(SLEEP_TIME)
