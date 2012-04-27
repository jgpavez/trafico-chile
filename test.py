# -*- coding: utf-8 -*-

import sys
import time
import couchdb
import os
from urllib2 import HTTPError
from couchdb.design import ViewDefinition
from kml__util import createKML 
from geopy import geocoders

subjects = ['trafico',
            'tráfico',
            'taco',
            'accidente',
            'automotriz'
            ]

articles = ['el',
            'en',
            'entre',
            'localizado'
            ]
            
hashtags = ['@',
            '#'
            ]


_last_update = 0
def sinceDateMapper(doc):
    from dateutil.parser import parse
    from datetime import datetime as dt
    _date = list(dt.timetuple(parse(('{0[1]} {0[2]} {0[3]} {0[4]}'.format(doc['created_at'].split(' ')))[:-3])))
    yield(_date,doc)
def getDocs():
    DB = 'trafico_chile'
    server = couchdb.Server('http://localhost:5984')
    db = server[DB]

    view = ViewDefinition('trafico_chile','by_date_time',sinceDateMapper,language='python')
    view.sync(db)
    docs = []
    for row in db.view('trafico_chile/by_date_time',startkey=list(time.gmtime(time.time()-3600.*50.))):
        _last_update = list(time.gmtime(time.time()))
        docs.append(db.get(row.id))
    return docs

def getLocationFromText(text):
        # text analysys
    text_location = text.lower()
    for part in text_location.split(' '):
        if part in subjects or part in articles or part[0] in hashtags:
            text_location = text_location.replace(part,'')
    # obtain location

    g = geocoders.Google('maps.google.cl')
    while True:
        num_errors = 0
        try:
            results = g.geocode(text_location.encode('utf-8'))
            break
        except HTTPError, e:
            num_errors += 1
            if num_errors >= 3:
                #log error
                sys.exit()
    print results
    (place,(lat,lon)) = results
    return  (text,place,(lat,lon))

    # return a name for the file that encapsulates the actual date
def getKMLFileName():
    return 'kml_' + str(_last_update).replace(' ','_') + '.kml'
    # Create KML to plot in google maps
def createKMLMap():
    docs = getDocs()
    place_coords = []
    kml_items = {}
    for doc in docs:
        place_coords.append(getLocationFromText(doc['text']))
    kml_items = [{'label':label, 'coords' : '%s,%s' % (coords[0],coords[1]),'text':text} for (text,label,coords) in place_coords]
    kml = createKML(kml_items)
    if not os.path.isdir('kml_out'):
        os.mkdir('kml_out')
    kml_name = getKMLFileName() 
    f = open('kml_out' + kml_name,'w')
    f.write(kml)
    return kml
print createKMLMap()
