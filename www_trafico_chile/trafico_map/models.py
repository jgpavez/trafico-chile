# -*- coding: utf-8 -*-
from django.db import models
import sys
import time
import os
import couchdb
import logging
from urllib2 import HTTPError
from couchdb.design import ViewDefinition
from kml__util import createKML
from geopy import geocoders

LOGGER_OUT = '/home/juan/trafico_chile/log/web.log'

subjects = ['trafico',
            'tráfico',
            'taco',
            'accidente',
            'automotriz'
            ]

articles = ['el',
            'en',
            'entre',
            'localizado',
            'frente'
            ]
            
hashtags = ['@',
            '#'
            ]

# Setting logger
logger = logging.getLogger('trafico_chile_web')
fl = logging.FileHandler(LOGGER_OUT)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fl.setFormatter(formatter)
logger.addHandler(fl)
logger.setLevel(logging.DEBUG)


def sinceDateMapper(doc):
    from dateutil.parser import parse
    from datetime import datetime as dt
    _date = list(dt.timetuple(parse(('{0[1]} {0[2]} {0[3]} {0[4]}'.format(doc['created_at'].split(' ')))[:-3])))
    yield(_date,doc)
class TraficoMap(models.Model):
    
    # Mapper for couchdb view
    def __init__(self):
        self._last_update = ''

    # Obtain the docs of the last 1 hour
    def getDocs(self):
        DB = 'trafico_chile'
        server = couchdb.Server('http://localhost:5984')
        db = server[DB]

        view = ViewDefinition('trafico_chile','by_date_time',sinceDateMapper,language='python')
        view.sync(db)
        docs = []
        for row in db.view('trafico_chile/by_date_time',startkey=list(time.gmtime(time.time()-3600.*2000))):
            self._last_update = time.strftime('%d_%b_%Y_%H_%M_%S',list(time.gmtime(time.time())))
            docs.append(db.get(row.id))
        return docs
    
    # Obtain location from text, principal function
    # Ver 1.
    def getLocationFromText(self,text):
        # text analysys
        text_location = text.lower()
        for part in text_location.split(' '):
            if part in subjects or part in articles or part[0] in hashtags:
                text_location = text_location.replace(part,'')
        if text_location.find('chile') == -1:
            text_location  = text_location + ' chile'

        # obtain location

        g = geocoders.Google('maps.google.cl')
        while True:
            num_errors = 0
            try:
                results = g.geocode(text_location.encode('utf-8'),exactly_one=False)
                break
            except HTTPError, e:
                num_errors += 1
                if num_errors >= 3:
                #log error
                    sys.exit()
        (place,(lat,lon)) = results[0]
        return  (text,place,[(lat,lon)])

    # return a name for the file that encapsulates the actual date
    def getKMLFileName(self):
        return 'kml_' + self._last_update + '.kml'
    # Create KML to plot in google maps
    def createKMLMap(self):
        docs = self.getDocs()
        place_coords = []
        kml_items = {}
        location = []
        temp_coords = []
        for doc in docs:
            location = self.getLocationFromText(doc['text'])
            temp_coords = location[2]
            logger.info(temp_coords[0])
            logger.info('location lat %d lon %d' % (temp_coords[0][0], temp_coords[0][1]))
#            if location[2][0]  < -18.187 and location[2][0] > -50.785 and location[2][1] > -69.757 and location[2][1] > -74.119:
            place_coords.append(location)
        kml_items = [{'text': text, 'label':label, 'coords' : '%s,%s' % coords[0]} for (text,label,coords) in place_coords]
        logger.info('kml ' + kml_items[0]['coords'])
        kml = createKML(kml_items)
        if not os.path.isdir('/home/juan/trafico_chile/www_trafico_chile/static/'):
            os.mkdir('/home/juan/trafico_chile/www_trafico_chile/static/')
        kml_name = self.getKMLFileName() 
        f = open('/home/juan/trafico_chile/www_trafico_chile/static/' + kml_name,'w')
        f.write(kml)
        f.close()
        return kml_name
