# -*- coding: utf-8 -*-
#!/usr/bin/python


###############################################
# Sub sucht rekursive einen Verzeichnisbaum
# nach einem Dateinamen durch
# und gibt dann den gesamten Pfad zurück
###############################################

import fnmatch
import os

def filesearch(startpfad,name=None):


    pfad = ''
    for pfad, dirs, files in os.walk(startpfad):
        #print pfad

        for filename in fnmatch.filter(files, name):

            erg_pfad =  os.path.join(pfad, filename)

    return erg_pfad