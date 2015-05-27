# -*- coding: utf-8 -*-
#!/usr/bin/python



from osgeo import ogr, osr, gdal
import os,sys,string, time, copy
from mod_diverses import *



################################################################
# sub merged sämtliche in einer (Pfadliste) vorkommenden Shapes
# zusammen und speichert sie an einem angegebenen Ort
# mit angegebnenem Namen
################################################################

def shapemerge(liste,auspfad,ausname,liste_feldnamen = None,polgem_name = None):



    # Das Standardbezugssystem hardcodiert...
    reffi = osr.SpatialReference()
    reffi.ImportFromEPSG(31254)


    # Geometrietyp wird anhand des ersten Shape der Liste
    # festgelegt und für den neuen Layer verwendet
    einshape = ogr.Open(liste[0])
    lyr  = einshape.GetLayer()
    geometrityp = lyr.GetGeomType()

    # Das Ausgangsshape wird angelegt
    out_driver = ogr.GetDriverByName( 'ESRI Shapefile' )
    # und falls ein glachnamiges existiert, dieses gelöscht
    if os.path.exists(str(auspfad + ausname)):
        out_driver.DeleteDataSource(str(auspfad+ausname))
    out_ds = out_driver.CreateDataSource(str(auspfad+ausname))
    out_layer = out_ds.CreateLayer(str(auspfad+ausname),srs = reffi, geom_type = geometrityp)    #das eigentliche Shape



    # Die Attributdefinition wird ebenfalls vom ersten Shape der Liste übernommen
    # Erstmal die FID anlegen
    feld = ogr.FieldDefn('FID', ogr.OFTInteger)
    out_layer.CreateField(feld)
    # Und dann die Felder...
    i = 0
    feldanzahl = lyr.GetLayerDefn().GetFieldCount()
    feldnamen = []
    # Anlegen der Attribute (Vorbild ist erstes Shape das gemerged wird)
    while i < feldanzahl:
        Fdefn = lyr.GetLayerDefn().GetFieldDefn(i)
        if not Fdefn.GetName() == 'FID': # FID hab ich grad angelegt, brauch ich nicht noch einmal
            out_layer.CreateField(Fdefn)
            feldnamen.append(Fdefn.GetName())
        i = i + 1

    # Ausnahmeregel für Grundstückshape
    # wir brauchen zusätzliche Felder
    if string.find(ausname, 'GST') > -1: # Zusätzliche Attribute für GST Flächen

            feld = ogr.FieldDefn('Area', ogr.OFTReal)
            out_layer.CreateField(feld)

            feld = ogr.FieldDefn('KG_GST', ogr.OFTString)
            feld.SetWidth(10)
            out_layer.CreateField(feld)


            feld = ogr.FieldDefn('GSTNR', ogr.OFTString)
            feld.SetWidth(10)
            out_layer.CreateField(feld)

            feld = ogr.FieldDefn('PGEM_NAME', ogr.OFTString)
            feld.SetWidth(20)
            out_layer.CreateField(feld)

    # Ausnahmeregel für Grundstücksnummernshape
    # wir brauchen zusätzliche Felder
    if string.find(ausname, 'GNR') > -1: # Masstabsattribut für GNR Shape

            feld = ogr.FieldDefn('MST', ogr.OFTInteger)
            out_layer.CreateField(feld)



    # nun wird die Liste der zu mergenden Shapes
    # abgearbeitet
    fid = 0
    for file in liste:

        # Eingangsshape
        einshape = ogr.Open(file)
        lyr = einshape.GetLayer()  # das eigentliche shape

        #so wärs wenn das maßstabsfeld noch verwendet wird,
        #das ist aber anscheinend nicht mehr der Fall wie das DXF zeigt
        # der Wert ist nämlich im Shape GST den wir ins GNR Shape eintragen sollten
        ############################################################################

        #if string.find(ausname, 'GNR') > -1: # Zusätzliche Attribute für GNR Flächen - Masstabsfeld
            #gst_shape = ogr.Open(str(auspfad + ausname).replace('GNR','GST'))
            #lyr_gst = gst_shape.GetLayer()

        #############################################################################

        for feat in lyr:
            out_feat = ogr.Feature(out_layer.GetLayerDefn())
            out_feat.SetField('FID',fid)

            for feld in feldnamen:
                wert = feat.GetField(feld)
                out_feat.SetField(feld,wert)

            out_feat.SetGeometry(feat.GetGeometryRef().Clone())

            if string.find(ausname, 'GST') > -1: # Zusätzliche Attribute für GST Flächen

                out_feat.SetField('area', feat.GetGeometryRef().GetArea())
                inhalt = out_feat.GetFieldAsString('KG') + '-' + out_feat.GetFieldAsString('GNR')
                out_feat.SetField('KG_GST', inhalt)
                inhalt = out_feat.GetFieldAsString('KG') + out_feat.GetFieldAsString('GNR')
                out_feat.SetField('GSTNR', inhalt)
                #print polgem_name
                out_feat.SetField('PGEM_NAME', str(polgem_name))
                #out_feat.SetField('FID',fid)

            if string.find(ausname, 'GNR') > -1: # Zusätzliche Attribute für GNR Flächen - Masstabsfeld

                #so wärs wenn das maßstabsfeld noch verwendet wird,
                #das ist aber anscheinend nicht mehr der Fall wie das DXF zeigt
                ##########################################################################
                #nummer = out_feat.GetFieldAsString('GNR').strip()
                #mst = 2
                #lyr_gst.ResetReading()  # Unbedingt den Cursor an den Anfang stellen
                #for feat_gst in lyr_gst:
                    #if feat_gst.GetFieldAsString('GNR').strip() == nummer:
                        #mst = feat_gst.GetFieldAsInteger('MST') * 2 # BEV ist leider inkonsistent, deshalb Wert verdoppeln
                #out_feat.SetField('MST', mst)
                #############################################################################


                out_feat.SetField('MST', 2) # wir setzen einfach 2 (Grüße Nummern 2 Meter) ins Feld ein

            out_layer.CreateFeature(out_feat)

            fid = fid + 1


    # und raus damit auf die Festplatte
    out_layer.SyncToDisk()

    #noch den index anlegen
    index_anlegen(out_ds,out_layer.GetName(), liste_feldnamen)



##########################################################################################
# Diese Modul vereint die Geometrie aller Objekte in einem Shape zu EINEM einzigen Objekt
# und gibt die Geometrie zurück oder speichert sie als Layer in einem Shape -
# abhängig von den Übergabeparameter
##########################################################################################
def shapeunion(einpfad,einname,auspfad,ausname, einlayer = None, lyr_dummy = None):

    # Geometrietyp wird anhand des ersten Shape der Liste
    # festgelegt und für den neuen Layer verwendet
    if einlayer == None:
        einshape = ogr.Open(einpfad+einname)
        lyr_in  = einshape.GetLayer()
    else:
        lyr_in  = einlayer
    geometrityp = lyr_in.GetGeomType()


    ###################################################
    # memory layer anlegen - damits schneller geht
    ##################################################

    # variant using the virtual file system method
    # mem_drv_in = ogr.GetDriverByName( 'ESRI Shapefile' )
    # mem_shp_in = mem_drv_in.CreateDataSource( str('/vsimem/dummy.shp') )
    # variant using the memory driver method
    mem_drv_in = ogr.GetDriverByName( 'Memory' )
    mem_shp_in = mem_drv_in.CreateDataSource( 'dummy')
    lyr_mem_in = mem_shp_in.CopyLayer(lyr_in,'dummy')  # das shape wird in den memory layer kopiert

    # Das ausgangsshape im memorybuffer wird angelegt
    # auch hier wieder zwei Varianten
    # mem_drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
    # mem_shp_out = mem_drv_in.CreateDataSource( str('/vsimem/dummy.shp') )
    # mem_drv_out = ogr.GetDriverByName( 'Memory' )
    # mem_shp_out = mem_drv_in.CreateDataSource( 'dummy_2')
    # lyr_mem_out = mem_shp_out.CreateLayer('dummy',geom_type = geometrityp)  # das shape wird in den memory layer kopiert


    # Attribute sind beim dissolve eigentlich sinnlos und werden nicht erzeugt
    outfeature = object()
    gemi_2= object()
    i = 0   #Featurezähler

    for feature in lyr_mem_in:
        gemi = feature.GetGeometryRef()

        if not i < 1:   # alles bis auf das erste Feature
            dummy = gemi.Union(gemi_2).Clone()    # gemi_2 wird neu als union
            gemi_2 = dummy.Clone()
            dummy = None
        elif i < 1: # das erste Feature
            outfeature = ogr.Feature(feature.GetDefnRef())  # nur beim ersten mal!
            gemi_2 = gemi.Clone()    # die startgeometrie

        i = i +1


    #######################################
    # geometrie ins outfeatureobject schreiben
    #######################################
    outfeature.SetGeometry(ogr.ForceToLineString(gemi_2))

    # lyr_mem_out.CreateFeature(outfeature)
    # lyr_dummy = lyr_mem_out

    # Cursor an den Anfang setzen
    # lyr_mem_out.ResetReading()


    # wird ein lyerobjekt übergeben
    # gibts das ergebnis auch so zurück und ende
    if not (einlayer == None):
        return outfeature

        #return lyr_mem_out

    # wurde ein shapepfad übergeben, gehts hier weiter
    # das Shape wird ins Filesystem geschrieben

    ##############################################
    # das endergebbnisshape, nun am filesystem
    ##############################################
    drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
    if os.path.exists(str(auspfad + ausname)):
        drv_out.DeleteDataSource(str(auspfad+ausname))
    ds_out = drv_out.CreateDataSource(str(auspfad+ausname))  # beim Shape ist Datasource bereits das File selbst
    lyr_out = ds_out.CreateLayer(str(ausname),geom_type = geometrityp)    # der eigentliche Layer (beim Shape ist das immer nur einer pro DS9



    # nun alles ins Shape am Filesystem schreiben
    # Copylayer Methode hat nicht funktioniert, keine Ahnung wieso!!
    # deshalb mit schleife - ist eh nur ein Objekt eigentlich
    #for feat in lyr_mem_out:
    lyr_out.CreateFeature(outfeature)


    return


