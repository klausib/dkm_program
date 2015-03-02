# -*- coding: utf-8 -*-
#!/usr/bin/python

from osgeo import ogr, osr, gdal
import os,sys
from shapely.wkb import *
from shapely.affinity import *

###################################################
# Setzen der Indices
###################################################

def index_anlegen(ds,layername,liste_feldnamen = None):

    #den räumlichen Index gleich anlegen
    ds.ExecuteSQL('create spatial index on ' + layername)


    #den Attributiven Index anlegen
    if not liste_feldnamen == None and len(liste_feldnamen) > 0:
        #feldnamenIn = din.getElementsByTagName("FieldName") #Diese Node im XNL enhält die Spaltenname mit Index!
        #for feldname in liste_feldnamen:
            #idx.append(feldname.firstChild.data)



        for indi in liste_feldnamen:
            query = str('create index on ' + layername + ' using ' + indi + '')
            ds.ExecuteSQL(query)




def set_geom_at(geom,X,Y, shiftx = 0, shifty = 0, rot = None, mst = None):

##    X_cent = geom.Boundary().Centroid().GetX()
##    Y_cent = geom.Boundary().Centroid().GetY()
##
##    dx =X - X_cent
##    dy = Y - Y_cent


    wkb_exp = geom.ExportToWkb()
    geom_wkb = loads(wkb_exp)   #aus der shapely

    X_cent = geom_wkb.bounds[0] + (geom_wkb.bounds[2] - geom_wkb.bounds[0])/2
    Y_cent = geom_wkb.bounds[1] + (geom_wkb.bounds[3] - geom_wkb.bounds[1])/2

##    X_cent = geom_wkb.envelope.bounds[0] + (geom_wkb.envelope.bounds[2] - geom_wkb.envelope.bounds[0])/2
##    Y_cent = geom_wkb.envelope.bounds[1] + (geom_wkb.envelope.bounds[3] - geom_wkb.envelope.bounds[1])/2


    dx = X - X_cent
    dy = Y - Y_cent



    #print str(geom_wkb.bounds)

    if (not mst == None) and mst > 0.1:
        shiftx = shiftx*mst/2
        shifty = shifty*mst/2


    #tmp = translate(geom_wkb,dx,dy,0)
    tmp = translate(geom_wkb,dx+shiftx,dy+shifty,0)
##
##    if not rot == None:
##        tmp = rotate(tmp,rot)

##    tmp = object()
    if (not rot == None) and rot > 0.1:
        #tmp = rotate(geom_wkb,rot)
        tmp = rotate(tmp,rot,(X,Y))
        #print str(X) + ' ' + str(Y)

##    tmp = translate(tmp,dx+shiftx,dy+shifty,0)

    if (not mst == None) and mst > 0.1:
        #print str(mst/2)
        tmp = scale(tmp,mst/2,mst/2)
        # bei verkelienerung oder vergrößerung muss korrigiert werden




##    liste = list(tmp)   #Generator Objekt zur Liste konvertieren
##
##    if len(liste) > 1:
##        logroutine(log_error,('ACHTUNG: Beim Erzeugen der KG Fläche gab es mehrere Polygone für die KG').decode('utf8') + ' ' + kgname + '\r',False)

##    depp_wkb = dumps(liste[0])  #sollte nur ein Element sein

    return dumps(tmp)