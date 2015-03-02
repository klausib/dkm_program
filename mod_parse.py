# -*- coding: utf-8 -*-
#!/usr/bin/python

from osgeo import ogr, osr, gdal
import os,sys, string, logging
from mod_diverses import *



def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)





######################################################
# Das Umwandeln von Text in Geometrie mit
# gleicher Form und Größe - Anhand von Vorlagenshapes
######################################################

def parse(log_error, input_path, input_name, output_path, output_name, typ, spaltenname_symbol, spaltenname_rotation = None, spaltenname_groesse = None,path_to_lookup_shape = 'shape_vorlagen/', name_of_lookup_shape = 'vorlage_dkm.shp'):



    #Das Standardbezugssystem hardcodiert...
    reffi = osr.SpatialReference()
    reffi.ImportFromEPSG(31254)

    # erstmal das Vorlagenshape oeffnen
    if not os.path.exists(input_path + input_name):
        print 'Vorlagenshape nicht gefunden'
        return


    # vorlagenshape oeffnen
    vorlagenshape = ogr.Open(path_to_lookup_shape + name_of_lookup_shape)
    lyr_vorlage  = vorlagenshape.GetLayer()


    # eingangsshape oeffnen
    eingangssgape = ogr.Open(input_path + input_name)
    lyr_input  = eingangssgape.GetLayer()


    #ausgangsshape anlegen - allerdinhs bei den nutzungssymbole, tja
    #da muss man zweimal reinschreiben, weil die attributtabelle unlogisch aufgebaut ist
    drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
    if os.path.exists(str(output_path + output_name)):
        drv_out.DeleteDataSource(str(output_path + output_name))

    ds_out = drv_out.CreateDataSource(str(output_path + output_name))  #beim Shape ist Datasource bereits das File selbst
    lyr_out = ds_out.CreateLayer(str(output_name),srs = reffi)    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)
##    elif os.path.exists(str(output_path + output_name)) and not loeschen:
##        ds_out = ogr.Open(str(output_path + output_name))
##        lyr_out  = ds_out.GetLayer()
##
##    else:
##        ds_out = drv_out.CreateDataSource(str(output_path + output_name))  #beim Shape ist Datasource bereits das File selbst
##        lyr_out = ds_out.CreateLayer(str(output_name),srs = reffi)    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)

    # Feature ID Spalte, sollte immer dabei sein, sonst gehts automatisch,
    # aber so find ich es eleganter
    Fid_feld = ogr.FieldDefn('FID', ogr.OFTInteger)
    # Fid_feld.SetWidth(11)
    lyr_out.CreateField(Fid_feld)
    # Ausnahme für die Nutzungssymbole, hier benötigen wir noch
    #zusätzliche Attribute
    if output_name == 'nutzungs_symbole.shp':
            # Das Feld für die ID definieren und hinzufügen
            id_feld = ogr.FieldDefn('ID', ogr.OFTInteger)
            #id_feld.SetWidth(4)
            lyr_out.CreateField(id_feld)


    feat_defn = lyr_out.GetLayerDefn()

    feat_id = 0
    for feature in lyr_input:

        lookupwert = None
        lookupwert2 = None
        if output_name == 'nutzungs_symbole.shp':
            #so, was haben wir eigentlich
            lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
            lookupwert2 = string.strip(feature.GetFieldAsString('NS_RECHT'))

            # Ach die DKM, nochmal nacbessern
            if lookupwert == '0':# and lookupwert2 != '0':
                lookupwert = string.strip(feature.GetFieldAsString('NS_RECHT'))
                lookupwert2 = None
            if lookupwert2 == '0':# and lookupwert2 != '0':
                lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
                lookupwert2 = None


##        elif output_name == 'sonstige_symbole.shp':
##            lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
##            if lookupwert == None:
##                continue

        # Bei den FEstpunkten wirds wirklich kompliziert
        # leider
        elif output_name == 'festpunkt_symbole.shp':
            lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
            lookupwert2 = string.strip(feature.GetFieldAsString('KZ_IND'))
            if lookupwert == "TP":     #Triangulierungspunkte können verschieden ausschauen
                    if lookupwert2[:1] == "T":
                        lookupwert = "9TP/K"
                        lookupwert2 = None
                    elif lookupwert2[:1] == "J" or lookupwert2[:1] == "K" or lookupwert2[:1] == "L" or lookupwert2[:1] == "M" or lookupwert2[:1] == "N" or lookupwert2[:1] == "S" or lookupwert2[:1] == "W":
                        lookupwert = "9TP/H"
                        lookupwert2 = None
                    else:
                        lookupwert = "9TP"
                        lookupwert2 = None

            elif lookupwert == "EP":
                lookupwert = "9EP"    #Einschaltpunkt
                lookupwert2 = None
            elif lookupwert == "PP" or lookupwert == "MP":
                lookupwert = "9PP"    #polygonpunkt bzw Meßpunkt sind gleich
                lookupwert2 = None
            elif lookupwert == "HP":
                lookupwert = "9HP"    #Höhenpunkt
                lookupwert2 = None

        else:
            lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))


        rot = None
        if not spaltenname_rotation == None:
            rot = feature.GetFieldAsDouble(spaltenname_rotation)

        mst = None
        if not spaltenname_groesse == None:
            mst = feature.GetFieldAsDouble(spaltenname_groesse)


        #print lookupwert
        lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + lookupwert + '\'')

        symbi_feat = lyr_vorlage.GetNextFeature()    # es darf nur eines geben

        # Wird im Vorlagenshape nix gefunden, aus welchem GRund auch immer
        # müssen wir das Feature auslassen und mit dem Nächsten weitermachen
        # natürlich brauchts einen Logeintrag
        if symbi_feat is None:
            logroutine(log_error, ('Für ').decode('utf8') + output_path + '/' + output_name + ' wurde das Symbol ' + lookupwert + ' nicht gefunden!\r' ,False)
            continue


        shiftx = symbi_feat.GetFieldAsDouble('SHIFTX')
        shifty = symbi_feat.GetFieldAsDouble('SHIFTY')
        symbi_geom = symbi_feat.GetGeometryRef()
        X = feature.GetGeometryRef().GetX()
        Y = feature.GetGeometryRef().GetY()

##        X = feature.geometry().GetX()
##        Y = feature.geometry().GetY()

##        if not spaltenname_rotation == None:
##            geom_neu = set_geom_at(symbi_geom,X,Y,rot)
##        else:
##            geom_neu = set_geom_at(symbi_geom,X,Y)

        geom_neu = set_geom_at(symbi_geom,X,Y,shiftx,shifty,rot,mst)

        #outfeature = feature.Clone()
        outfeature = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben
        outfeature.SetGeometry(ogr.CreateGeometryFromWkb(geom_neu))
        outfeature.SetField('FID',feat_id)

        #Zusatzattribut für Nutzungssymbole

        if output_name == 'nutzungs_symbole.shp':
            wert = feature.GetFieldAsInteger('NS_RECHT')
            if wert > 0:
                outfeature.SetField('ID', 1)
                #print str(outfeature.GetFieldIndex('ID'))
                #print str(outfeature.IsFieldSet('ID'))
            else:
                #outfeature.SetField('ID', 0)
                outfeature.SetField('ID', 0)
            #print str(feature.GetFieldAsInteger('MST_NS'))


        lyr_out.CreateFeature(outfeature)


        # Nutzungssymbole müssen manchmal übereinander gelegt werden.....also nochmal das Ganze
        if not lookupwert2 is None:
            #print lookupwert
            lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + lookupwert2 + '\'')

            symbi_feat = lyr_vorlage.GetNextFeature()    # es darf nur eines geben

            # Wird im Vorlagenshape nix gefunden, aus welchem GRund auch immer
            # müssen wir das Feature auslassen und mit dem Nächsten weitermachen
            # natürlich brauchts einen Logeintrag
            if symbi_feat is None:
                logroutine(log_error, ('Für ').decode('utf8') + output_path + '/' + output_name + ' wurde das Symbol ' + lookupwert + ' nicht gefunden!\r' ,False)
                continue


            shiftx = symbi_feat.GetFieldAsDouble('SHIFTX')
            shifty = symbi_feat.GetFieldAsDouble('SHIFTY')
            symbi_geom = symbi_feat.GetGeometryRef()
            X = feature.GetGeometryRef().GetX()
            Y = feature.GetGeometryRef().GetY()

    ##        X = feature.geometry().GetX()
    ##        Y = feature.geometry().GetY()

    ##        if not spaltenname_rotation == None:
    ##            geom_neu = set_geom_at(symbi_geom,X,Y,rot)
    ##        else:
    ##            geom_neu = set_geom_at(symbi_geom,X,Y)

            geom_neu = set_geom_at(symbi_geom,X,Y,shiftx,shifty,rot,mst)

            #outfeature = feature.Clone()
            outfeature = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben
            outfeature.SetGeometry(ogr.CreateGeometryFromWkb(geom_neu))

            #Zusatzattribut für Nutzungssymbole

            if output_name == 'nutzungs_symbole.shp':
                wert = feature.GetFieldAsInteger('NS_RECHT')
                if wert > 0:
                    outfeature.SetField('ID', 1)
                    #print str(outfeature.GetFieldIndex('ID'))
                    #print str(outfeature.IsFieldSet('ID'))
                else:
                    #outfeature.SetField('ID', 0)
                    outfeature.SetField('ID', 0)
                #print str(feature.GetFieldAsInteger('MST_NS'))


            lyr_out.CreateFeature(outfeature)

        feat_id = feat_id + 1
    index_anlegen(ds_out,lyr_out.GetName())


