﻿# -*- coding: utf-8 -*-
#!/usr/bin/python



import sqlite3, os, sys, copy
import logging,string,shutil
from Main_Window import *
from PyQt4 import QtCore, QtGui, QtXml
from osgeo import ogr, osr, gdal
from mod_filesearch import *
from mod_shapemerge import *
from mod_diverses import *
from mod_parse import *
from shapely.wkb import *
from shapely.ops import *
from shapely import wkb
from shapely import ops








# Logroutine
def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)







###################################################################
# WICHTIG: Grundlegendes Verhalten der OGR/GDAl Lib wird so
# festgelegt und gilt für alle Teile des Programmes während der
# Laufzeit
###################################################################



gdal.UseExceptions()    # WICHTIG: Um GDAL/OGR Fehle r als Laufzeitfehler abfangen
                        # und im Code behandeln zu können
gdal.SetConfigOption( "SQLITE_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!
gdal.SetConfigOption( "PG_LIST_ALL_TABLES", "YES" ) #Sonst können keine geometrielosen Tabellen gefunden werden!!!


# Ein Log für alle Fälle

log_error = logging.getLogger('log1')

fh_error = logging.FileHandler('error.log','w','utf8')

form_error = logging.Formatter("%(asctime)s %(levelname)s %(message)s","%d.%m.%y-%H:%M")

fh_error.setFormatter(form_error)


log_error.addHandler(fh_error)
log_error.setLevel(logging.ERROR)



#############################################################################
# Klassendefinition: Startcode und geerbte die GUI
#####################################################################

class Dialog (QtGui.QMainWindow, Ui_Main_Window):
#class Dialog (QtGui.QDialog, Ui_frmOptions):




    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_Main_Window.__init__(self)


        self.FileDialog = QtGui.QFileDialog()
        self.FileDialog.setFileMode(QtGui.QFileDialog.Directory)

        # und nun was spezielles: Ohne den nachfolgenden
        # Call wird das Widget, das im Designer erzeugt wurde,
        # nicht dargestellt!!
        self.setupUi(self)


        self.einpfad = ''
        self.auspfad = ''




        try:


            #Öffnen der Steuertabelle
            #Sqlite DB mit der Kopierliste öffnen
            #Die Steuertabelle einlesen

            if os.path.exists('dkm_lookup.sqlite'):
                self.db  = sqlite3.connect("dkm_lookup.sqlite")
            else:
                raise SystemExit




            self.db.row_factory = sqlite3.Row    #für den Zugriff auf die einzelnen Spalten mit dem Spaltennamen
            #Den Datenbankkursor instanzieren
            assert self.db != None, "Steuertabelle: Datenbankobjekt ist None"   # Datenbankobjekt ist nicht erzeugt worden: Assertion Fehler wird ausgelöst
            cursor_sqlite = self.db.cursor()

        except:
            print 'Steuertabelle nicht gefunden - Programm stoppt'
            logroutine(log_error, 'Steuertabelle nicht gefunden - Programm stoppt' ,False)
            sys.exit(0) # Komplettabrruch










        self.db.row_factory = sqlite3.Row    #für den Zugriff auf die einzelnen Spalten mit dem Spaltennamen

        #Den Datenbankkursor instanzieren
        assert self.db != None, "Steuertabelle: Datenbankobjekt ist None"   # Datenbankobjekt ist nicht erzeugt worden: Assertion Fehler wird ausgelöst
        self.cursor_sqlite = self.db.cursor()


        #Die Auswahlabfrage ausführen: Alle Gemeinden die konvertiert werden sollen
        self.cursor_sqlite.execute("select * from pol where aktual = 'ja'")

        #Alle passenden records auf einmal einlesen
        self.rows = self.cursor_sqlite.fetchall()
        if len(self.rows) > 0:
            row = self.rows[0]   #zurücksetzen
        else:
            row = []


    ##########################################################
    # hier gehts los wenn man die DKM Generierung startet
    ##########################################################
    def start(self):

        #Hauptschleife, alle records abarbeiten
        #das bedeutet alle zu aktualisierenden
        #Shapes, Tabellen, Dateien
        if self.auspfad == '' or self.einpfad == '':
            QtGui.QMessageBox.critical(None, "Achtung",("Bitte Verzeichnisse auswählen!").decode("utf-8"))
            return

        if not (os.path.exists(self.auspfad) or os.path.exists(self.einpfad)):
            QtGui.QMessageBox.critical(None, "Achtung",("Bitte Verzeichnisse neu wählen!").decode("utf-8"))
            return

        # Überordner
        if not os.path.exists(self.auspfad + "dkm/"):
                os.mkdir(self.auspfad + "dkm/")


        gemeinde_pfadliste = []


        # Haupschleife: Geht Gemeinde für Gemeinde durch
        # ACHTUNG: Für Vorarlberg gesamt werden einfach alle
        # durchgerechneten Gemeinden hergenommen. Wenn man also
        # nur ein paar auswählt, dann besteht Vorarlberg gesamt
        # nur aus diesen
        for row in self.rows:
            pgem_name = row[0]
            pgem_gesn = row[2]
            pfad = self.auspfad + "dkm/" + pgem_name

            # Gemeindeordner
            if not os.path.exists(pfad):
                os.mkdir(pfad)

            # Die Unterverzeichnisse jeder Gemeinde
            if not os.path.exists(pfad + '/Grenzpunkte'):
                os.mkdir(pfad + '/Grenzpunkte')
            if not os.path.exists(pfad + '/Nutzung'):
                os.mkdir(pfad + '/Nutzung')
            if not os.path.exists(pfad + '/Grundstuecke'):
                os.mkdir(pfad + '/Grundstuecke')
            if not os.path.exists(pfad + '/Sonstiges'):
                os.mkdir(pfad + '/Sonstiges')




            # Zuweisen der Katastralgemeindenamen zur jeweiligen politischen Gemeinde
            # Aus der Datenbank
            if pgem_name == "Vorarlberg": # Bei Vorarlberg werden nur alle Gemeinden gemerged
                self.cursor_sqlite.execute("select PGEM_NAME from pol where not PGEM_NAME = \'Vorarlberg\'")
                row_of_kats =  self.cursor_sqlite.fetchall()
                gemeinde_pfadliste = []
                for kat in row_of_kats:
                    gemeinde_pfadliste.append(str(self.auspfad) + "dkm/" + str(kat[0]))
            else:
                self.cursor_sqlite.execute("select Kgem_gesnr from kat where Pgem_gesnr = " + str(pgem_gesn))


            if pgem_name != 'Vorarlberg':

                # Alle zur pol. Gemeinde/Vorarlberg gehörenden Katastralgemeinden
                # Die Shapes der KGs werden zur pol. Gemeinde zusammengefügt
                row_of_kats =  self.cursor_sqlite.fetchall()
                pfadlist = []
                for kat in row_of_kats:
                    upper_path = filesearch(str(self.einpfad), str(kat[0]) + "FPT" + "_V2.shp")
                    pfadlist.append(os.path.dirname(str(upper_path)) + '/' + str(kat[0]))
                    #print os.path.dirname(upper_path)


                # Die einzelnen ursprünglichen DKM Layer werden zusammengeführt
                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "FPT" + "_V2.shp")

                shapemerge(filelist,pfad + '/Sonstiges/','FPT.shp',['PNR'],pgem_name) # macht auch die indices


                filelist = []



                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "GST" + "_V2.shp")
                shapemerge(filelist,pfad + '/Grundstuecke/','GST.shp',None,pgem_name,self.cursor_sqlite) # macht auch die indices

                # ACHTUNG: Zuerst GST und dann GNR!!
                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "GNR" + "_V2.shp")
                shapemerge(filelist,pfad + '/Grundstuecke/','GNR.shp',None,pgem_name) # macht auch die indices


                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "NFL" + "_V2.shp")
                shapemerge(filelist,pfad + '/Nutzung/','NFL.shp',None,pgem_name) # macht auch die indices


                # gebaudefläche.shp erzeugen
                drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
                if os.path.exists(str(pfad + '/Nutzung/gebaeudeflaechen.shp')):
                    drv_out.DeleteDataSource(str(pfad + '/Nutzung/gebaeudeflaechen.shp'))
                ds_out = drv_out.CreateDataSource(str(pfad + '/Nutzung/gebaeudeflaechen.shp'))  #beim Shape ist Datasource bereits das File selbst

                kg_ds = ogr.Open(str(pfad + '/Nutzung/NFL.shp'))
                kg_lyr = kg_ds.GetLayer()
                kg_lyr.SetAttributeFilter('NS = 41')

                lyr = ds_out.CopyLayer(kg_lyr, 'gebaeudeflaechen.shp')

                # die FID Spalte korrigieren
                feat_id = 0
                for feat in  lyr:
                    feat.SetField('FID',feat_id)
                    lyr.SetFeature(feat)    #sonst wird die Änderung nicht übernommen!!
                    feat_id = feat_id + 1
                lyr.SyncToDisk()

                # noch den index anlegen - dafür gibts ein eigenes sub
                index_anlegen(ds_out,'gebaeudeflaechen')


                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "NSL" + "_V2.shp")
                shapemerge(filelist,pfad + '/Nutzung/','NSL.shp',None,pgem_name) # macht auch die indices


                # sonstige_grenzen.shp erzeugen
                drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
                if os.path.exists(str(pfad + '/Sonstiges/sonstige_grenzen.shp')):
                    drv_out.DeleteDataSource(str(pfad + '/Sonstiges/sonstige_grenzen.shp'))
                ds_out = drv_out.CreateDataSource(str(pfad + '/Sonstiges/sonstige_grenzen.shp'))  #beim Shape ist Datasource bereits das File selbst

                kg_ds = ogr.Open(str(pfad + '/Nutzung/NSL.shp'))
                kg_lyr = kg_ds.GetLayer()
                kg_lyr.SetAttributeFilter('NSL = 4')

                lyr = ds_out.CopyLayer(kg_lyr, 'sonstige_grenzen.shp')

                 # die FID Spalte korrigieren
                feat_id = 0
                for feat in  lyr:
                    feat.SetField('FID',feat_id)
                    lyr.SetFeature(feat)    #sonst wird die Änderung nicht übernommen!!
                    feat_id = feat_id + 1
                lyr.SyncToDisk()

                # noch den index anlegen - dafür gibts ein eigenes sub
                index_anlegen(ds_out,'sonstige_grenzen')



                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "NSY" + "_V2.shp")
                shapemerge(filelist,pfad + '/Nutzung/','NSY.shp',None,pgem_name) # macht auch die indices

                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "SGG" + "_V2.shp")
                shapemerge(filelist,pfad + '/Grenzpunkte/','SGG.shp',None,pgem_name) # macht auch die indices

                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "SSB" + "_V2.shp")
                shapemerge(filelist,pfad + '/Sonstiges/','SSB.shp',None,pgem_name) # macht auch die indices

                filelist = []

                for pfad_in in pfadlist:
                    filelist.append (pfad_in + "VGG" + "_V2.shp")
                shapemerge(filelist,pfad + '/Sonstiges/','VGG.shp',None,pgem_name) # macht auch die indices


                ###########################################################
                # kgflaeche.shp erzeugen - mit Hilfe von Shapely
                # und mit Attributen füllen die aus
                ##############################################################

                 # Das Standardbezugssystem hardcodiert...
                reffi = osr.SpatialReference()
                reffi.ImportFromEPSG(31254)

                drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
                if os.path.exists(str(pfad + '/Sonstiges/kgflaeche.shp')):
                    drv_out.DeleteDataSource(str(pfad + '/Sonstiges/kgflaeche.shp'))
                ds_out = drv_out.CreateDataSource(str(pfad + '/Sonstiges/kgflaeche.shp'))  #beim Shape ist Datasource bereits das File selbst
                lyr_out = ds_out.CreateLayer(str('kgflaeche.shp'), srs = reffi)    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)


                # Feature ID Spalte, sollte immer dabei sein, sonst gehts automatisch,
                # aber so find ich es eleganter
                Fid_feld = ogr.FieldDefn('FID', ogr.OFTInteger)
                lyr_out.CreateField(Fid_feld)
                # Das Feld für die KGNR definieren und hinzufügen
                kg_feld = ogr.FieldDefn('KG', ogr.OFTString)
                kg_feld.SetWidth(5)
                lyr_out.CreateField(kg_feld)
                # Das Feld für den Gemeindenamen
                feld = ogr.FieldDefn('PGEM_NAME', ogr.OFTString)
                feld.SetWidth(20)
                lyr_out.CreateField(feld)

                feat_defn = lyr_out.GetLayerDefn()

                fid = 0
                for file in filelist:

                    # reiner KG Name
                    kgname = os.path.basename(file)
                    kgname = os.path.splitext(kgname) #Gibt ein Tuple zurück
                    kgname = string.replace(kgname[0],'VGG_V2','')

                    # VGG der jeweiligen KG öffnen
                    kg_ds = ogr.Open(str(file))
                    kg_lyr = kg_ds.GetLayer()
                    kg_lyr.SetAttributeFilter('VGG = 3 or VGG = 4 or VGG = 5 or VGG = 6 or VGG = 8 or VGG = 9')
                    feat_union = (shapeunion(None,None,None,None,kg_lyr))   # Linestrings vereinen - brauchts das wirklich??

                    geom_poly = feat_union.GetGeometryRef()

                    wkb_exp = geom_poly.ExportToWkb()
                    shp_geom = loads(wkb_exp)   # aus der shapely
                    tmp = polygonize (shp_geom)

                    liste = list(tmp)   # Generator Objekt zur Liste konvertieren

                    if len(liste) > 1:
                        logroutine(log_error,('ACHTUNG: Beim Erzeugen der KG Fläche gab es mehrere Polygone für die KG').decode('utf8') + ' ' + kgname + '\r',False)

                    depp_wkb = dumps(liste[0])  #sollte nur ein Element sein

                    feat_union = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben
                    feat_union.SetGeometry(ogr.CreateGeometryFromWkb(depp_wkb))
                    feat_union.SetField('KG', kgname)
                    feat_union.SetField( 'FID', fid)
                    feat_union.SetField('PGEM_NAME', str(pgem_name))
                    lyr_out.CreateFeature(feat_union)
                    fid = fid + 1


                #noch den index anlegen
                index_anlegen(ds_out,'kgflaeche')

            ####################################################################
            # Fläche der politischen Gemeinden - nur für gesamt Vorarlberg
            ####################################################################
            if pgem_name == 'Vorarlberg':


                # Das Standardbezugssystem hardcodiert...
                reffi = osr.SpatialReference()
                reffi.ImportFromEPSG(31254)

                drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
                if os.path.exists(str(pfad + '/Sonstiges/Gemeinden.shp')):
                    drv_out.DeleteDataSource(str(pfad + '/Sonstiges/Gemeinden.shp'))
                ds_out = drv_out.CreateDataSource(str(pfad + '/Sonstiges/Gemeinden.shp'))  #beim Shape ist Datasource bereits das File selbst
                lyr_out = ds_out.CreateLayer(str('Gemeinden.shp'), srs = reffi)    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)


                # Feature ID Spalte, sollte immer dabei sein, sonst gehts automatisch,
                # aber so find ich es eleganter
                Fid_feld = ogr.FieldDefn('FID', ogr.OFTInteger)
                lyr_out.CreateField(Fid_feld)
                # Das Feld für die PGEM_GESNR definieren und hinzufügen
                pg_feld = ogr.FieldDefn('PGEM_GESNR', ogr.OFTInteger)
                pg_feld.SetWidth(5)
                lyr_out.CreateField(pg_feld)

                feat_defn = lyr_out.GetLayerDefn()

                fid = 0
                for file in gemeinde_pfadliste:

                    # reiner PG Name
                    pgem = string.replace(str(file),self.auspfad + "dkm/",'')

                    # Die Auswahlabfrage ausführen: Auswahl der passenden Pol Gemeindenummer
                    sqlstring = "select * from pol where PGEM_NAME = '" + pgem + "'"
                    self.cursor_sqlite.execute(sqlstring)
                    #Alle passenden records auf einmal einlesen
                    rows = self.cursor_sqlite.fetchall()

                    # Es darf nur einen Record geben, sonst ist was faul
                    r_i = 0
                    for count in rows:
                        r_i = r_i + 1
                    if r_i != 1:
                        logroutine(log_error,('ACHTUNG: Beim Erzeugen des Gemeinden Shapes gibt es Probleme').decode('utf8') + ' ' + pgem + '\r',False)
                        continue # mit dem rest gehts weiter, es fehlt dann eine Gemeinde


                    pgem_gesn = rows[0][2] # die Pol. Gemeindenummer

                    file = file + '/Sonstiges/VGG.shp'  # der Pfad zum benötigten Shape


                    # VGG der jeweiligen KG öffnen
                    kg_ds = ogr.Open(str(file))
                    kg_lyr = kg_ds.GetLayer()
                    kg_lyr.SetAttributeFilter('VGG = 4 or VGG = 5 or VGG = 6 or VGG = 8 or VGG = 9')    #  pol. grenzen
                    feat_union = (shapeunion(None,None,None,None,kg_lyr))   # Linestrings vereinen - brauchts das wirklich??

                    geom_poly = feat_union.GetGeometryRef()

                    wkb_exp = geom_poly.ExportToWkb()
                    shp_geom = loads(wkb_exp)   # aus der shapely
                    tmp = polygonize (shp_geom)

                    liste = list(tmp)   # Generator Objekt zur Liste konvertieren
                    if len(liste) != 1:
                        logroutine(log_error,('ACHTUNG: Beim Erzeugen der Polgem Fläche gab es mehrere Polygone für die Gemeinde').decode('utf8') + ' ' + pgem + '\r',False)
                        continue
                    depp_wkb = dumps(liste[0])  #sollte nur ein Element sein


                    feat_union = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben
                    feat_union.SetGeometry(ogr.CreateGeometryFromWkb(depp_wkb))

                    feat_union.SetField('PGEM_GESNR', pgem_gesn)
                    feat_union.SetField( 'FID', fid)
                    lyr_out.CreateFeature(feat_union)
                    fid = fid + 1


                #noch den index anlegen
                index_anlegen(ds_out,'Gemeinden')

            ####################################################
            # Erzeugen der Shape- Texte und Shape- Symbole
            ####################################################

            # ACHTUNG: Vorarlberg muss ganz am Schluss gerechnet werden, wenn alle anderen Gemeinden fertig sin
            # und das auch im selber Rechnedurchlauf!! Es werden für Vorarlberg nur die Gemeinden genommen
            # die im Sleben Programmlauf erzeugt wurden, wie auch Vorarlberg. Wenn nur eine gerechnet wird, dann nur eine etc...
            if pgem_name == 'Vorarlberg':

                #alles auscodieren machts üebrsichtlicher

                #--------------------
                # Ordner Grenzpunkte
                #--------------------

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    #print einzelgem
                    file = (einzelgem + '/Grenzpunkte/grenzpunkt_symbole.shp')
                    vlbg_pfadlist.append(str(file))
                shapemerge(vlbg_pfadlist,pfad + '/Grenzpunkte/','grenzpunkt_symbole.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grenzpunkte/grenzpunkt_nummern.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grenzpunkte/','grenzpunkt_nummern.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grenzpunkte/SGG.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grenzpunkte/','SGG.shp') # macht auch die indices


                #--------------------
                # Ordner Nutzung
                #--------------------

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Nutzung/nutzungs_symbole.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Nutzung/','nutzungs_symbole.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Nutzung/gebaeudeflaechen.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Nutzung/','gebaeudeflaechen.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Nutzung/NFL.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Nutzung/','NFL.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Nutzung/NSL.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Nutzung/','NSL.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Nutzung/NSY.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Nutzung/','NSY.shp') # macht auch die indices

                #--------------------
                # Ordner Sonstiges
                #--------------------

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/sonstige_symbole.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','sonstige_symbole.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/sonstige_texte.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','sonstige_texte.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/festpunkt_symbole.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','festpunkt_symbole.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/sonstige_grenzen.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','sonstige_grenzen.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/FPT.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','FPT.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/SSB.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','SSB.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/VGG.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','VGG.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Sonstiges/kgflaeche.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Sonstiges/','kgflaeche.shp') # macht auch die indices




                #--------------------
                # Ordner Grundstuecke
                #--------------------

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grundstuecke/grundstueck_nummern.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grundstuecke/','grundstueck_nummern.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grundstuecke/grundstueck_nummern_mittelgross.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grundstuecke/','grundstueck_nummern_mittelgross.shp') # macht auch die indices


                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grundstuecke/grundstueck_nummern_gross.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grundstuecke/','grundstueck_nummern_gross.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grundstuecke/GST.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grundstuecke/','GST.shp') # macht auch die indices

                vlbg_pfadlist = []
                for einzelgem in gemeinde_pfadliste:
                    file = (einzelgem + '/Grundstuecke/GNR.shp')
                    vlbg_pfadlist.append(str(file))

                shapemerge(vlbg_pfadlist,pfad + '/Grundstuecke/','GNR.shp') # macht auch die indices





            else:
                # Grenzpunkt Nummern und Symbole
                parse(pgem_name, log_error, str(pfad) + '/Grenzpunkte/','SGG.shp', str(pfad) + '/Grenzpunkte/','grenzpunkt_symbole.shp','symbol','TYP')
                parse(pgem_name, log_error, str(pfad) + '/Grenzpunkte/','SGG.shp', str(pfad) + '/Grenzpunkte/','grenzpunkt_nummern.shp','text', None,'PNR', 'ROT_PNR', None, 'RW_PNR', 'HW_PNR')


                # Nutzungssysmbole
                parse(pgem_name, log_error, str(pfad) + '/Nutzung/','NSY.shp', str(pfad) + '/Nutzung/','nutzungs_symbole.shp','symbol','NS',None,'ROT_NS','MST_NS')

                # Sonstige Symbole und sonstige Texte
                parse(pgem_name, log_error, str(pfad) + '/Sonstiges/','SSB.shp', str(pfad) + '/Sonstiges/','sonstige_symbole.shp','symbol','TYP',None, 'ROT_NR')
                parse(pgem_name, log_error, str(pfad) + '/Sonstiges/','SSB.shp', str(pfad) + '/Sonstiges/','sonstige_texte.shp','text', None,'TEXT', 'ROT_NR', 'TEXTGR')

                # Grundstück Nummern
                parse(pgem_name, log_error, str(pfad) + '/Grundstuecke/','GNR.shp', str(pfad) + '/Grundstuecke/','grundstueck_nummern.shp','text', None,'GNR', 'ROT_GNR', 'MST','RW_PFNR', 'HW_PFNR', 1) # konstanter MAßstab
                parse(pgem_name, log_error, str(pfad) + '/Grundstuecke/','GNR.shp', str(pfad) + '/Grundstuecke/','grundstueck_nummern_mittelgross.shp','text', None,'GNR', 'ROT_GNR', 'MST','RW_PFNR', 'HW_PFNR', 1.5) # konstanter MAßstab
                parse(pgem_name, log_error, str(pfad) + '/Grundstuecke/','GNR.shp', str(pfad) + '/Grundstuecke/','grundstueck_nummern_gross.shp','text', None,'GNR', 'ROT_GNR', 'MST','RW_PFNR', 'HW_PFNR', 2) # konstanter MAßstab


                # Festpunkt Symbole
                parse(pgem_name, log_error, str(pfad) + '/Sonstiges/','FPT.shp', str(pfad) + '/Sonstiges/','festpunkt_symbole.shp','symbol','TYP')


            shutil.copyfile("dkm.qgs", str(pfad) + "/dkm.qgs")


            # Für Vorarlberg gesamt (muss in der SQL Lite Abfrage als letztes kommen und davor
            # alle Gemeinden fertig sein
            gemeinde_pfadliste.append(pfad)

            #Auf erledigt stellen
            #print 'dkm_main' + pgem_name
            self.cursor_sqlite.execute("update pol set aktual = 'erledigt' where pgem_name = '" + pgem_name + "'")
            self.db.commit() #


    # Einlesen der Pfade: Quellpfad der DKM Daten
    @QtCore.pyqtSignature("")
    def on_ButtonPathEin_clicked(self):
        if (self.FileDialog.exec_()):
            auswahl = self.FileDialog.selectedFiles()
            if len(auswahl) == 1:
                self.einpfad = auswahl[0] + os.sep

                #raus = self.d.toString()
                self.lblPathEin.setText(self.einpfad.replace("\\","/"))
            else:
                QtGui.QMessageBox.critical(None, "Achtung",("Bitte richtiges Verzeichnis auswählen!").decode("utf-8"))
                return

    # Einlesen der Pfade: Zielpfad des Ergebnis der Umwandlung
    @QtCore.pyqtSignature("")
    def on_ButtonPathAus_clicked(self):
        if (self.FileDialog.exec_()):
            auswahl = self.FileDialog.selectedFiles()
            if len(auswahl) == 1:
                self.auspfad = auswahl[0] + os.sep

                #raus = self.d.toString()
                self.lblPathAus.setText(self.auspfad.replace("\\","/"))
            else:
                QtGui.QMessageBox.critical(None, "Achtung",("Bitte richtiges Verzeichnis auswählen!").decode("utf-8"))
                return

     # Zum close Event
    @QtCore.pyqtSignature("")
    def on_btnStart_clicked(self):
        self.start()

    # Zum close Event
    @QtCore.pyqtSignature("")
    def on_btnEnd_clicked(self):
        self.closeEvent()



    #Reimplamentierung des closeEvents des Event Handlers!
    #Wird immer vom Event Handler ausgelöst, wenn auf das schließen Kästchen x geklickt wird
    #Wird hier auch vom Abbrechen Button verwendet, deshalb ist die Variable event = None gesetzt, da
    #das cleccked Signal nicht übergibt (was eine fehlermeldung bewirken würde), wohl aber
    # das x Kästchen wenn geklicket
    def closeEvent(self,event = None):

        self.close()
        # QgsApplication.exitQgis()


# Das obligate Main (damit Coe auch als SUB ausgeführt werden kann)


def main(argv):
    import sys

    app = QtGui.QApplication(argv) # Applikationsobjekt
    window = Dialog()   # Die GUI
    window.show()
    sys.exit(app.exec_())   # Die Event Loop

# als main start6en oder optinal auch zum Import
# als Modul vorbereiten
# stackexchange.......When the Python interpreter reads a source file, it executes all of the code found in it.
# Before executing the code, it will define a few special variables.
# For example, if the python interpreter is running that module (the source file) as the main program, it sets the special __name__ variable to have a value "__main__".
# If this file is being imported from another module, __name__ will be set to the module's name......

if __name__ == '__main__':

    main(sys.argv)