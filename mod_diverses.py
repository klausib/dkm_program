# -*- coding: utf-8 -*-
#!/usr/bin/python

from osgeo import ogr, osr, gdal
import os,sys
from shapely.wkb import *
from shapely.affinity import *
from shapely.ops import *

###################################################
# Dieses Sub erzeugt sowohl den räumlichen Index
# beim übergebnen Shape
# als auch die attributiven Indices wenn eine Liste
# mit feldnamen mitgegeben wird
###################################################
def index_anlegen(ds,layername,liste_feldnamen = None):

    #den räumlichen Index gleich anlegen
    ds.ExecuteSQL('create spatial index on ' + layername)


    #den Attributiven Index anlegen - gemäß der Liste mit den feldnamen
    if not liste_feldnamen == None and len(liste_feldnamen) > 0:
        for indi in liste_feldnamen:
            query = str('create index on ' + layername + ' using ' + indi + '')
            ds.ExecuteSQL(query)



###################################################
# Dieses Sub schiebt die erzeugten Symbole
# oder Texte an die richtige Stelle und
# dreht alles noch falls ein Drehwinkel angegeben -
# und verändert die Größe wenn ein Maßstabsfeld vorhanden ist.
# Dazu benötigen wir die Shaply Libs.
###################################################
def set_geom_at(geom,X,Y, shiftx = 0, shifty = 0, rot = None, mst = None, text_sym = ''):

    # OGR Geometry in Shaply Geometrie umwandeln
    wkb_exp = geom.ExportToWkb()
    geom_wkb = loads(wkb_exp)   #aus der shapely

    if text_sym == 'text':
        X_cent = geom_wkb.bounds[0]
        Y_cent = geom_wkb.bounds[1]
    else:   # auch für GST
        X_cent = geom_wkb.bounds[0] + (geom_wkb.bounds[2] - geom_wkb.bounds[0])/2
        Y_cent = geom_wkb.bounds[1] + (geom_wkb.bounds[3] - geom_wkb.bounds[1])/2


    dx = X - X_cent
    dy = Y - Y_cent

    # Zuerst an die Richtig Position schieben (wird übergeben)
    # möglicherweise ein ShiftX, hängt vom Text (z.B g, q, j,  kommt vor)
    # und Symbol ab
    tmp = translate(geom_wkb, dx + shiftx, dy + shifty, 0)

    # dann wird gedreht (um den Einfügepunkt)
    if (not rot == None) and rot > 0.1:
        tmp = rotate(tmp, rot, (X,Y))


    # Nun die Größe der Buchstaben und
    # Symbole festlegen. Saumäßig komplizierter
    # Algorithmus
    if text_sym == 'text':
        if ( mst == None) : # Keine Maßstabsspalte angegeben
            mst = 1 / (geom_wkb.bounds[3] - geom_wkb.bounds[1])
            tmp = scale(tmp, mst, mst, origin = (X,Y))
        else:   # es gibt eine Maßstabsspalte die indiv. die Größe angibt
            tmp = scale(tmp,mst/2,mst/2, origin = (X,Y))
    else:   # Beis Symbolen ists leichter
        if (not mst == None) and mst > 0.1:
            tmp = scale(tmp,mst/2,mst/2)


    return dumps(tmp)

