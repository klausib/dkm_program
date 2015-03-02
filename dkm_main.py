# -*- coding: utf-8 -*-
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
##from mod_generate_polygon import *
from shapely.wkb import *
from shapely.ops import *
##from qgis.core import *
##from qgis.gui import *
##from qgis.analysis import *
##from shapely import *







# Logroutine
def logroutine(log_error, text,flag):

    log_error.error(unicode(text),exc_info=flag)





# Environment variable QGISHOME must be set to the install directory
# before running the application
qgis_prefix = os.getenv("QGISHOME")


###################################################################
#WICHTIG: Grundlegendes Verhalten der OGR/GDAl Lib wird so
#festgelegt und gilt für alle Teile des Programmes während der
#Laufzeit
###################################################################



gdal.UseExceptions()    # WICHTIG: Um GDAL/OGR Fehler als Laufzeitfehler abfangen
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



class Dialog (QtGui.QMainWindow, Ui_Main_Window):
#class Dialog (QtGui.QDialog, Ui_frmOptions):




    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_Main_Window.__init__(self)
        #Ui_frmOptions.__init__(self)

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
            #db  = sqlite3.connect("kopierlistee.sqlite")

            if os.path.exists('dkm_lookup.sqlite'):
                db  = sqlite3.connect("dkm_lookup.sqlite")
                #print os.path.exists('dkm_lookup.sqlite')
            else:

                #log_error.error('Steuertabelle nicht gefunden')
                #logroutine(log_error,"Fehler: Oeffnen der Steuertabelle fehlgeschlagen\r",False)

                raise SystemExit
                #raise Exception



            db.row_factory = sqlite3.Row    #für den Zugriff auf die einzelnen Spalten mit dem Spaltennamen
            #Den Datenbankkursor instanzieren
            assert db != None, "Steuertabelle: Datenbankobjekt ist None"   # Datenbankobjekt ist nicht erzeugt worden: Assertion Fehler wird ausgelöst
            cursor_sqlite = db.cursor()

        except:

            sys.exit(0)










        db.row_factory = sqlite3.Row    #für den Zugriff auf die einzelnen Spalten mit dem Spaltennamen

        #Den Datenbankkursor instanzieren
        assert db != None, "Steuertabelle: Datenbankobjekt ist None"   # Datenbankobjekt ist nicht erzeugt worden: Assertion Fehler wird ausgelöst
        self.cursor_sqlite = db.cursor()


        #Die Auswahlabfrage ausführen: Alle Gemeinden die konvertiert werden sollen
        self.cursor_sqlite.execute("select * from pol where aktual = 'ja'")

        #Alle passenden records auf einmal einlesen
        self.rows = self.cursor_sqlite.fetchall()
        if len(self.rows) > 0:
            row = self.rows[0]   #zurücksetzen
        else:
            row = []


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

        # Haupschleife: Geht Gemeinde für Gemeinde durch
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
            if pgem_name == "Vorarlberg":
                self.cursor_sqlite.execute("select Kgem_gesnr from kat")
            else:
                self.cursor_sqlite.execute("select Kgem_gesnr from kat where Pgem_gesnr = " + str(pgem_gesn))

            # Alle zur pol. Gemeinde/Vorarlberg gehörenden Katastralgemeinden
            row_of_kats =  self.cursor_sqlite.fetchall()

            # Die einzelnen DKM Layer werden zusammengeführt
            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "FPT" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Sonstiges/','FPT.shp',['PNR']) # macht auch die indices




            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "GNR" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Grundstuecke/','GNR.shp') # macht auch die indices


            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "GST" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Grundstuecke/','GST.shp',None,pgem_name) # macht auch die indices



            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "NFL" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Nutzung/','NFL.shp') # macht auch die indices

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
            #noch den index anlegen
            index_anlegen(ds_out,'gebaeudeflaechen')



            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "NSL" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Nutzung/','NSL.shp') # macht auch die indices

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
            #noch den index anlegen
            index_anlegen(ds_out,'sonstige_grenzen')



            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "NSY" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Nutzung/','NSY.shp') # macht auch die indices

            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "SGG" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Grenzpunkte/','SGG.shp') # macht auch die indices

            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "SSB" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Sonstiges/','SSB.shp') # macht auch die indices

            filelist = []
            for kat in row_of_kats:
                filelist.append (filesearch(str(self.einpfad),  str(kat[0]) + "VGG" + "_V2.shp"))
            shapemerge(filelist,pfad + '/Sonstiges/','VGG.shp') # macht auch die indices

            # kgflaeche.shp erzeugen - mit Hilfe von Shapely
            drv_out = ogr.GetDriverByName( 'ESRI Shapefile' )
            if os.path.exists(str(pfad + '/Sonstiges/kgflaeche.shp')):
                drv_out.DeleteDataSource(str(pfad + '/Sonstiges/kgflaeche.shp'))
            ds_out = drv_out.CreateDataSource(str(pfad + '/Sonstiges/kgflaeche.shp'))  #beim Shape ist Datasource bereits das File selbst
            lyr_out = ds_out.CreateLayer(str('kgflaeche.shp'))    #der eigentliche Layer (beim Shape ist das immer nur einer pro DS)


            # Feature ID Spalte, sollte immer dabei sein, sonst gehts automatisch,
            # aber so find ich es eleganter
            Fid_feld = ogr.FieldDefn('FID', ogr.OFTInteger)
            # Fid_feld.SetWidth(11)
            lyr_out.CreateField(Fid_feld)
            # Das Feld für die KGNR definieren und hinzufügen
            kg_feld = ogr.FieldDefn('KG', ogr.OFTString)
            kg_feld.SetWidth(5)
            lyr_out.CreateField(kg_feld)

            feat_defn = lyr_out.GetLayerDefn()

            fid = 0
            for file in filelist:

                #reiner KG Name
                kgname = os.path.basename(file)
                kgname = os.path.splitext(kgname) #Gibt ein Tuple zurück
                kgname = string.replace(kgname[0],'VGG_V2','')

                # VGG der jeweiligen KG öffnen
                kg_ds = ogr.Open(str(file))
                kg_lyr = kg_ds.GetLayer()
                kg_lyr.SetAttributeFilter('VGG = 3 or VGG = 4 or VGG = 8 or VGG = 9')
                feat_union = (shapeunion(None,None,None,None,kg_lyr))   #Linestrings vereinen - brauchts das wirklich??
                #geom_poly = ogr.ForceToPolygon(feat_union.GetGeometryRef())
                geom_poly = feat_union.GetGeometryRef()

                wkb_exp = geom_poly.ExportToWkb()
                shp_geom = loads(wkb_exp)   #aus der shapely
                tmp = polygonize (shp_geom)

                liste = list(tmp)   #Generator Objekt zur Liste konvertieren

                if len(liste) > 1:
                    logroutine(log_error,('ACHTUNG: Beim Erzeugen der KG Fläche gab es mehrere Polygone für die KG').decode('utf8') + ' ' + kgname + '\r',False)

                depp_wkb = dumps(liste[0])  #sollte nur ein Element sein

                feat_union = ogr.Feature(feat_defn) # ACHTUNG: ohne korrekte featuredefn lassen sich die Attribute nicht schreiben
                feat_union.SetGeometry(ogr.CreateGeometryFromWkb(depp_wkb))
                feat_union.SetField('KG', kgname)
                feat_union.SetField( 'FID', fid)
                lyr_out.CreateFeature(feat_union)
                fid = fid + 1


            #noch den index anlegen
            index_anlegen(ds_out,'kgflaeche')




            ####################################################
            # Erzeugen der Shape- Texte und Shape- Symbole
            ####################################################

            # Grenzpunkt Nummern und Symbole
            parse(log_error, str(pfad) + '/Grenzpunkte/','SGG.shp', str(pfad) + '/Grenzpunkte/','grenzpunkt_symbole.shp','symbol','TYP')
            # parse(str(pfad) + '/Grenzpunkte/','SGG.shp', str(pfad) + '/Grenzpunkte/','grenzpunkt_nummern.shp','text','PNR')
            #noch den index anlegen
            #index_anlegen(str(pfad) + '/Grenzpunkte/','grenzpunkt_symbole')


            # Nutzungssysmbole
            parse(log_error, str(pfad) + '/Nutzung/','NSY.shp', str(pfad) + '/Nutzung/','nutzungs_symbole.shp','symbol','NS','ROT_NS','MST_NS')
            #parse(str(pfad) + '/Nutzung/','NSY.shp', str(pfad) + '/Nutzung/','nutzungs_symbole.shp','symbol','NS_RECHT','ROT_NS','MST_NS')
            #noch den index anlegen
            #index_anlegen(str(pfad) + '/Nutzung/','nutzungs_symbole')

            # Sonstige Symbole
            parse(log_error, str(pfad) + '/Sonstiges/','SSB.shp', str(pfad) + '/Sonstiges/','sonstige_symbole.shp','symbol','TYP', 'ROT_NR')
            #noch den index anlegen
            #index_anlegen(str(pfad) + '/Sonstiges/','sonstige_symbole')

            # Festpunkt Symbole
            parse(log_error, str(pfad) + '/Sonstiges/','FPT.shp', str(pfad) + '/Sonstiges/','festpunkt_symbole.shp','symbol','TYP')
            #noch den index anlegen
            #index_anlegen(str(pfad) + '/Sonstiges/','festpunkt_symbole')


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
                QgsApplication.exitQgis()
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
                QgsApplication.exitQgis()
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




def main(argv):
    import sys

    app = QtGui.QApplication(argv)
     # create Qt application
##
##      # Initialize qgis libraries
##    QgsApplication.setPrefixPath(qgis_prefix, True)
##
##    # load providers
##    QgsApplication.initQgis()
    #KG Fläche Union über alle Grundstücke: Operation über QGIS API
    #gstLyr = QgsVectorLayer("D:/dkm/dkm/Feldkirch/Grundstuecke/GST.shp", "GST","ogr")
    #gstLyr = QgsVectorLayer("D:/depp.shp", "depp","ogr")

    window = Dialog()

    window.show()

    sys.exit(app.exec_())

# als main start6en oder optinal auch zum Import
# als Modul vorbereiten
# stackexchange.......When the Python interpreter reads a source file, it executes all of the code found in it.
# Before executing the code, it will define a few special variables.
# For example, if the python interpreter is running that module (the source file) as the main program, it sets the special __name__ variable to have a value "__main__".
# If this file is being imported from another module, __name__ will be set to the module's name......

if __name__ == '__main__':

    main(sys.argv)