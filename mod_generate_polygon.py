# -*- coding: utf-8 -*-
#!/usr/bin/python

# Generate Polygon Geometry from
# Input Geometries. Valid Input are Point or Linestring
# Types


from osgeo import ogr, osr, gdal


def generate_polygon(import_geometry):

    i = 0
    # print str(import_geometry.GetPoints())
    punkte = []
##    for point in import_geometry:
##        for depp in point.GetPoints():  # depp ist ein Tuple mit den Koordinaten
##            #print str(i) + ' DEPPILI ' + str(depp)
##            punkte.append(depp)
##            i = i+1
    ring = ogr.Geometry(ogr.wkbLinearRing)
    poly = ogr.Geometry(ogr.wkbPolygon)

##    for ddd in punkte:
##        ring.AddPoint(ddd[0], ddd[1])
##
    for point in import_geometry:
            print str(i) + ' DEPPILI ' + str(point)
            ring.AddGeometry(point)



    ring.CloseRings()
    poly.AddGeometry(ring)

    return poly