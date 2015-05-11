# -*- coding: utf-8 -*-

#!/usr/bin/python

from osgeo import ogr, osr, gdal
import os,sys, string, logging, math
from mod_diverses import *
from shapely.wkb import *
from shapely.affinity import *
from shapely.ops import *
from dbfpy.dbf import *





def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)



#gdal.SetConfigOption( "SHAPE_ENCODING", "cp1252")




######################################################
# Das Umwandeln von Text in Geometrie mit
# gleicher Form und Größe - Anhand von Vorlagenshapes
# Das Modul parse übernimmt die Hauptaufgabe für
# das Anlegen der Symbole. Bei den Texten
# wird nur das Ausgangsshape und die final Position
# durchgeführt (sow wie es für die Symbole auch gemacht
# wird, bei denen reicht das dann auch schon).
#  Der Text selber wird in einem Sub erzeugt
######################################################
def parse(log_error, input_path, input_name, output_path, output_name, typ, spaltenname_symbol = None, spaltenname_text = None, spaltenname_rotation = None, spaltenname_groesse = None, spaltenname_X = None, spaltenname_Y = None, gst_multiply = 1, path_to_lookup_shape = 'shape_vorlagen/', name_of_lookup_shape = 'vorlage_dkm.shp'):



    #Das Standardbezugssystem hardcodiert...
    reffi = osr.SpatialReference()
    reffi.ImportFromEPSG(31254)

    # erstmal prüfen ob das Vorlagenshape vorhanden
    if not os.path.exists(path_to_lookup_shape + name_of_lookup_shape):
        print 'Vorlagenshape nicht gefunden'
        logroutine(log_error, 'Vorlagenshape nicht gefunden' ,False)
        return

     # erstmal prüfen ob das eingangsshape vorhanden
    if not os.path.exists(input_path + input_name):
        print 'Eingangsshape nicht gefunden'
        logroutine(log_error, 'Eingangsshape nicht gefunden' ,False)
        return


    # vorlagenshape oeffnen - herkömmlich
    # vorlagenshape = ogr.Open(path_to_lookup_shape + name_of_lookup_shape)
    # lyr_vorlage  = vorlagenshape.GetLayer()

    # vorlagenshape oeffnen - in memory Layer einlesen
    vorlagenshape = ogr.Open(path_to_lookup_shape + name_of_lookup_shape)
    lyr_vorlage_tmp  = vorlagenshape.GetLayer()
    mem_vorlage = ogr.GetDriverByName( 'Memory' )
    mem_ds_vorlage = mem_vorlage.CreateDataSource( 'vorlage_mem' )
    lyr_vorlage = mem_ds_vorlage.CopyLayer(lyr_vorlage_tmp,'lyr_vorlage')


    # Dbase Objekt aus DBF des Vorlagenshape erzeugen (DBF Bibliothek)
    db = Dbf('./shape_vorlagen/vorlage_dkm.dbf')


    # eingangsshape oeffnen - herkömmlich
    # eingangssgape = ogr.Open(input_path + input_name)
    # lyr_input  = eingangssgape.GetLayer()

    # eingangsshape oeffnen - in memory
    eingangssgape = ogr.Open(input_path + input_name)
    lyr_input_tmp  = eingangssgape.GetLayer()
    mem_input = ogr.GetDriverByName( 'Memory' )
    mem_ds_input = mem_input.CreateDataSource( 'input_mem' )
    lyr_input = mem_ds_input.CopyLayer(lyr_input_tmp,'lyr_input' )


    #ausgangsshape anlegen - allerdings bei den nutzungssymbole, tja
    #da muss man zweimal reinschreiben, weil die attributtabelle unlogisch aufgebaut ist
    drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
    if os.path.exists(str(output_path + output_name)):
        drv_out.DeleteDataSource(str(output_path + output_name))

    ds_out = drv_out.CreateDataSource(str(output_path + output_name))  #beim Shape ist Datasource bereits das File selbst
    lyr_out = ds_out.CreateLayer(str(output_name),srs = reffi)    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)


    # Feature ID Spalte, sollte immer dabei sein, sonst gehts automatisch,
    # aber so find ich es eleganter
    Fid_feld = ogr.FieldDefn('FID', ogr.OFTInteger)
    lyr_out.CreateField(Fid_feld)




    # Ausnahme für die Nutzungssymbole, hier benötigen wir noch
    # zusätzliche Attribute
    if output_name == 'nutzungs_symbole.shp':
        # Das Feld für die ID definieren und hinzufügen
        id_feld = ogr.FieldDefn('ID', ogr.OFTInteger)
        lyr_out.CreateField(id_feld)

    # wird ein neues Feature erzeugt,
    # brauche ich eine feature Definition
    # die nehme ich vom Shape in das später
    #gespeichert wird
    feat_defn = lyr_out.GetLayerDefn()

    # Zähler initialisieren
    feat_id = 0


    # den Eingangslayer feature für feature durchgehen
    for feature in lyr_input:

        # initialize
        symbi_feat = None
        lookupwert = None   # enthalten Text oder die Symbolkennung
        lookupwert2 = None  # wenn überlagert werden soll
        y_vers = 0  # Versatz von Texten bei Buchstaben wie g, j, q etc.



        ###########################################################
        # hier die Symbolthemen (einfacher)
        ###########################################################
        if not (spaltenname_symbol == None) and (spaltenname_text == None):

            # für die nutzungssymbole sonderbehandlung
            if output_name == 'nutzungs_symbole.shp':
                #so, was haben wir eigentlich
                lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
                lookupwert2 = string.strip(feature.GetFieldAsString('NS_RECHT'))

                # nachkorrigieren, so ist halt die DKM
                if lookupwert == '0':# and lookupwert2 != '0':
                    lookupwert = string.strip(feature.GetFieldAsString('NS_RECHT'))
                    lookupwert2 = None
                if lookupwert2 == '0':# and lookupwert2 != '0':
                    lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))
                    lookupwert2 = None



            # Bei den Festpunkten wirds wirklich kompliziert
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

            # alle anderen Symbolthemen sind kein Problem
            else:
                lookupwert = string.strip(feature.GetFieldAsString(spaltenname_symbol))


            # Rotation gewünscht
            rot = None
            if not spaltenname_rotation == None:
                rot = feature.GetFieldAsDouble(spaltenname_rotation)

            # Vergrößern / Verkleinern gewünscht
            mst = None
            if not spaltenname_groesse == None:
                mst = feature.GetFieldAsDouble(spaltenname_groesse)

            # Position nicht aus Koordinate des Punktes 8Shape) sondern Attributtabelle
            X = None
            if not spaltenname_X == None:
                X = feature.GetFieldAsDouble(spaltenname_X)
            Y = None
            if not spaltenname_Y == None:
                Y = feature.GetFieldAsDouble(spaltenname_Y)


            # das feature für den entsprechenden Symboltyp filtern (gibt nur eines)
            lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + lookupwert + '\'')

            y_vers = 0 # Wert nur bei Text benötigt
            symbi_feat = lyr_vorlage.GetNextFeature()   # die passende Symbolgeometrie aus dem Vorlagenshape



        ###########################################################
        # hier NUR für die Text- und Nummernthemen (komplizierter)
        ###########################################################
        elif (spaltenname_symbol == None) and not (spaltenname_text == None):


            # Rotation gewünscht
            rot = None
            if not spaltenname_rotation == None:
                rot = feature.GetFieldAsDouble(spaltenname_rotation)

            # Vergrößern / Verkleinern gewünscht
            mst = None
            if not spaltenname_groesse == None:
                mst = feature.GetFieldAsDouble(spaltenname_groesse) * gst_multiply

            lookupwert = feature.GetFieldAsString(spaltenname_text) # Unser Text oder Nummer

            if lookupwert == 'None' or lookupwert == 'none':
                    continue

            # und nun das Zentrale: Der Text wird im Sub toText
            # in ein Liniefeature mit gleichem Aussehen umgewandelt
            # und dann als feature zurückgegeben
            ret_tmp = toText(lookupwert, lyr_vorlage, 0.66,db)  # liste wird zurückgegeben


            if ret_tmp is None:
                continue # next feature
            else:
                symbi_feat = ret_tmp[0]
                y_vers = ret_tmp[1]


            # Position nicht aus Koordinate des Punktes (Shape) sondern Attributtabelle
            X = None
            if not spaltenname_X == None:
                X = feature.GetFieldAsDouble(spaltenname_X)
            Y = None
            if not spaltenname_Y == None:
                Y = feature.GetFieldAsDouble(spaltenname_Y)



        ################################################################
        # nun wieder für Text und Symbole gemeinsam
        ################################################################

        # Wird im Vorlagenshape nix gefunden, aus welchem Grund auch immer
        # müssen wir das Feature auslassen und mit dem Nächsten weitermachen
        # natürlich brauchts einen Logeintrag
        if symbi_feat is None:
            logroutine(log_error, ('Für ').decode('utf8') + output_path + '/' + output_name + ' wurde das Symbol ' + (lookupwert).decode('utf8') + ' nicht gefunden!\r' ,False)
            continue

        # feature in OGR GEometrie umwandeln
        symbi_geom = symbi_feat.GetGeometryRef()

        # Gibts ein Shift
        shiftx = symbi_feat.GetFieldAsDouble('SHIFTX')
        shifty = symbi_feat.GetFieldAsDouble('SHIFTY') + y_vers

        # wenn keine Koordinaten aus der Attributtabelle
        # verwendet werden, dann die des Punktes aus dem Shape
        if Y == None or X == None:
            X = feature.GetGeometryRef().GetX()
            Y = feature.GetGeometryRef().GetY()

        # und jetzt an die richtige Position schieben,
        # rotieren und vergrößern/verkleinern falls notwendig
        geom_neu = set_geom_at(symbi_geom,X,Y,shiftx,shifty,rot,mst,typ)

        # ACHTUNG: BEV Daten sind leider sehr durcheinander: Grundstücksnummern haben eigene Rolle
        # Pfeilnummern und Grenzkatasterstriche werden hier wie Symbole hinzugefügt
        add_g = False
        add_p = False
        geom_neu_g = None
        geom_neu_p = None

        if string.find(output_name, 'grundstueck_nummern') > -1: # bei den Grundstücksnummernzusätzen den typ auf symbol setzen wegen Positionierung!
            typ = 'symbol'

            # Grenzkatasterstriche
            wert = feature.GetFieldAsString('RSTATUS').strip()
            if wert == 'G':
                #print lookupwert
                add_g = True
                lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + '9grenzkat' + '\'')


                # envelope returna minx,maxx,miny,maxy
                y_vers_g = (symbi_geom.GetEnvelope()[3] - symbi_geom.GetEnvelope()[2]) * 1.1 * gst_multiply
                #print str(symbi_geom.GetEnvelope())
                symbi_feat_g = lyr_vorlage.GetNextFeature() # there must be only one - and this one is fetched
                                                            # and will be later put on its correct position

                symbi_geom_g = symbi_feat_g.GetGeometryRef()
                geom_neu_g = set_geom_at(symbi_geom_g,X,Y,shiftx,shifty - y_vers_g,rot,mst,typ)


            # Pfeile bei Pfeilnummern
            wert = feature.GetFieldAsInteger('TYP')
            if wert == 3:

                add_p = True

                delta_x = feature.GetGeometryRef().GetX() - X
                delta_y = feature.GetGeometryRef().GetY() - Y
                pf_length = math.sqrt( math.pow(delta_x,2 ) +  math.pow(delta_x,2 ))

                lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + '9pfeil' + '\'')

                rot_p = rot = feature.GetFieldAsDouble('ROT_PF')

                symbi_feat_p = lyr_vorlage.GetNextFeature() # there must be only one - and this one is fetched
                                                            # and will be later put on its correct position


                symbi_geom_p = symbi_feat_p.GetGeometryRef()

                pfl = math.fabs(symbi_geom_p.GetEnvelope()[1] - symbi_geom_p.GetEnvelope()[0]) / -2


                geom_neu_p = set_geom_at(symbi_geom_p,feature.GetGeometryRef().GetX(),feature.GetGeometryRef().GetY(), pfl,0,rot_p,None,typ)


        # ein neues Feature instanzieren
        outfeature = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben

        # und dem Feature die Geometrie zuweisen
        if add_g:   # Grenzkatasterstriche
            geom_temp_g = loads(geom_neu_g)
            temp_g = geom_temp_g.union(loads(geom_neu))
            outfeature.SetGeometry(ogr.CreateGeometryFromWkb(dumps(temp_g)))
        elif add_p: # Pfeil bei Pfeilnummer
            geom_temp_p = loads(geom_neu_p)
            geom_temp_p = geom_temp_p.difference(loads(geom_neu).buffer(1.3))   # Pfeile werden beschnitten
            temp_p = geom_temp_p.union(loads(geom_neu))

            outfeature.SetGeometry(ogr.CreateGeometryFromWkb(dumps(temp_p)))
        else:   # der ganze Rest
            outfeature.SetGeometry(ogr.CreateGeometryFromWkb(geom_neu))


        # die Feature ID machen wir auch noch rein
        outfeature.SetField('FID',feat_id)


        # Genauso wie ein Zusatzattribut für Nutzungssymbole
        if output_name == 'nutzungs_symbole.shp':
            wert = feature.GetFieldAsInteger('NS_RECHT')
            if wert > 0:
                outfeature.SetField('ID', 1)
            else:
                outfeature.SetField('ID', 0)


        # so, nun endlich endlich das Feature ist fertig
        # und wird in den Layer eingefügt
        #lyr_out.CreateFeature(outfeature)



        ###############################################################################################
        # Symbole müssen manchmal übereinander gelegt werden.....also nochmal das Ganze
        # weils so schön war - aber zum Glück nur für Symbole - wenn lookupwert und lookupwert2 belegt
        ###############################################################################################
        if not lookupwert2 is None: # jaja übereinanderlegen
            lyr_vorlage.SetAttributeFilter('ZEICHEN = \'' + lookupwert2 + '\'')

            symbi_feat = lyr_vorlage.GetNextFeature()    # es darf nur eines geben

            # Wird im Vorlagenshape nix gefunden, aus welchem Grund auch immer
            # müssen wir das Feature auslassen und mit dem Nächsten weitermachen
            # natürlich brauchts einen Logeintrag
            if symbi_feat is None:
                logroutine(log_error, ('Für ').decode('utf8') + output_path + '/' + output_name + ' wurde das Symbol ' + lookupwert + ' nicht gefunden!\r' ,False)
                continue

            # Shift un Position erneut berechnen
            shiftx = symbi_feat.GetFieldAsDouble('SHIFTX')
            shifty = symbi_feat.GetFieldAsDouble('SHIFTY')
            symbi_geom = symbi_feat.GetGeometryRef()
            X = feature.GetGeometryRef().GetX()
            Y = feature.GetGeometryRef().GetY()

            # und positionieren
            geom_neu_ns = set_geom_at(symbi_geom,X,Y,shiftx,shifty,rot,mst)


            geom_temp_ns = loads(geom_neu_ns)
            temp_ns = geom_temp_ns.union(loads(geom_neu))

            outfeature.SetGeometry(ogr.CreateGeometryFromWkb(dumps(temp_ns)))


        # so, nun endlich endlich das Feature ist fertig
        # und wird in den Layer eingefügt
        lyr_out.CreateFeature(outfeature)

        feat_id = feat_id + 1

    index_anlegen(ds_out,lyr_out.GetName())

    db.close()

    # na endlich fertig


################################################################################
# dieses sub erzeugt aus Zahlen oder Texte linienfeatures die dem Text genau
# entsprechen und wie dieser aussehen.
################################################################################
def toText(lookupwert,lyr_vorlage, zwischenraum, db):


    symbi_feat = None
    offset = 0
    geo = None
    y_shift = 0


    objektliste = []
    lookupwert_utf = lookupwert.decode('utf8')  # bytestring erstmal in unicode umwandeln (codierung utf8 passt)

    for zeichen in lookupwert_utf:  # zeichen für zeichen durchgehen
        fea = None
        feat_add = None
        werti = None

        # leider hat die OGR versagt. Für einen Vergleich der Zeichen
        # geht nur die DBFPY Bibliothek, mit der die Dbase Datei der shapevorlage
        # übergeben wird
        for rec in db:

            if rec['ZEICHEN'].decode('latin1') == zeichen:  # dbase der shapevorlage durchgehen : Achtung, auch in unicode umwandeln
                werti = rec['ID']   # ID rauslesen
                lyr_vorlage.SetAttributeFilter('ID = ' + str(werti))    # Attribute Filter kann nun mit Hilfe der ID gesetzt werden (mit den ZEichen geht es leider nicht)
                fea = lyr_vorlage.GetNextFeature()  # betreffendes feature zurückgeben
                break # for schleife wird bei Treffer abgebrochen


        if werti is None:
            fea = None # wird als Leerzeichen behandelt, wenn nichts gefunden wird


        if fea is None:
            offset = offset + zwischenraum * 2  # einfach wie ein Leerzeichen, Space
            continue # zum nächsten Zeichen weiter

        geo = fea.GetGeometryRef()  # Geometrie des Zeichens als Linie


        # der anchfolgnde IF Block setzt den Text Zeichen
        # für ZEichen, oder besser Liniengeometrie für Liniengeometrie
        # zu einem Gesamten zusammen
        # Für die Geofunktionen brauchen wir die Shapely!!
        if not zeichen == ' ':

            feat_add = fea.Clone()
            geom_add = feat_add.GetGeometryRef()

            wkb_add = geom_add.ExportToWkb()
            geo_wkb_add = loads(wkb_add)    # aus der shapely - umwandeln in geometrieobjekt


            X_left = geo_wkb_add.bounds[0]
            Y_low = geo_wkb_add.bounds[1]

            dy = Y_low - geo_wkb_add.bounds[3]

            if zeichen == 'g' or zeichen == 'j' or zeichen == 'q' or zeichen == 'p' or zeichen == 'y':
                Y_low = Y_low - dy / 3
                y_shift = dy / 3    # Shift Korrektur für den ganzen Text, sonst sind g etc. und der Text auf einer Line

            if zeichen == '(' or zeichen == ')':
                Y_low = Y_low - dy  / 6
                y_shift = dy / 6    # Shift Korrektur für den ganzen Text, sonst sind ( etc. und der Text auf einer Line

            if zeichen == '-':
                Y_low = Y_low - (geo_wkb_add.bounds[2] - geo_wkb_add.bounds[0]) / 2

            tmp = translate(geo_wkb_add, -X_left + offset, -Y_low, 0)

            objektliste.append(tmp) # die Objektlieste enthält alle Linienfeatures die den TExt ausmachen
            offset = offset + (tmp.bounds[2] - tmp.bounds[0]) + zwischenraum


        else:
            # ein Leerzeichen, Space
            offset = offset + zwischenraum * 2


    if not feat_add is None:
        symbi_feat = feat_add.Clone()
        dodl = unary_union(objektliste) # Die einzelnen Geometrieen werden vereinigt
        symbi_feat.SetGeometry(ogr.CreateGeometryFromWkb(dumps(dodl)))
        return [symbi_feat, y_shift]    # Geometrie und Shift werden zurückgegeben
    else:
         return None
