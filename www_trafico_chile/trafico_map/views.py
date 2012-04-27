# Create your views here.
from  django.shortcuts import render_to_response
from trafico_map.models import TraficoMap

def index(request):
   trafico = TraficoMap() 
   kml = trafico.createKMLMap()
   kml_file = 'http://190.161.109.150/www_trafico_chile/static/test.kml' 
   return render_to_response('trafico_map/index.html',{'kml':str(kml_file)})
