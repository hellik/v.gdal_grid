#!/usr/bin/env python

"""
MODULE:    v.gdal_grid

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Calculates bbox of every geometry in a vector layer
           and writes a GDAL gdal_translate commands to extract
		   tiles matching the vector geometries bbox

COPYRIGHT: (C) 2016 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%module
#% description: writing gdal_translate commands to extract tiles matching the vector geometries bbox
#% keyword: vector
#% keyword: geometry
#% keyword: raster
#%end

#%option G_OPT_V_INPUT 
#% key: input
#% required: yes
#%end

#%flag
#% key: c
#% description: print minimum and maximum cats of vector
#% guisection: print
#%end

#%flag
#% key: b
#% description: print bounding box of vector layer
#% guisection: print
#%end

#%flag
#% key: t
#% description: print bounding box of vector geometries
#% guisection: print
#%end

#%option G_OPT_M_DIR
#% key: dir
#% description: Directory where the output will be found
#% required : no
#% guisection: output
#%end

#%option
#% key: prefix
#% type: string
#% key_desc: prefix
#% description: raster output prefix (must start with a letter)
#% guisection: output
#%end

#%option
#% key: raster
#% type: string
#% key_desc: input raster name
#% description: input raster name for the gdal_translate command
#% guisection: output
#%end

#%option
#% key: file
#% type: string
#% key_desc: file name
#% description: name of the file holding the gdal_translate command
#% guisection: output
#%end

#%flag
#% key: s
#% description: writing gdal_translate commands into a file
#% guisection: output
#%end

import sys
import os
import csv
import math
import shutil
import tempfile
import grass.script as grass
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Area
import xml.etree.ElementTree as etree

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():

    vector = options['input'].split('@')[0]
    directory = options['dir']
    print_min_max_cats = flags['c']
    print_bbox_vector = flags['b']
    print_bbox_vector_geometries = flags['t']
    export_cmds = flags['s']
    prefix = options['prefix']
    inraster = options['raster']
    filename = options['file']

    ######
    # define minimum and maximum cat in vector layer
    ######    
    vcats = grass.read_command("v.category", input = vector,
                                     option = "report",
                                     flags = "g",
                                     quiet = True)
		
    vcats_min = int(vcats.split()[8])
    vcats_max = int(vcats.split()[9])
    vcats_max_plus = vcats_max + 1	

    ######
    # print minimum and maximum cat in vector layer
    ###### 	
    if print_min_max_cats :

		grass.message( "min cat: %s max cat: %s" % (vcats_min, vcats_max))

    ######
    # print bbox of vector layer
    ###### 	
    if print_bbox_vector :
		# open vector
		vtopo = VectorTopo(vector)
		vtopo.open(mode = 'r')
		# bbox call
		bbox_vector = vtopo.bbox()
		# bbox north, south, west, east
		bbv_north = bbox_vector.north
		bbv_south = bbox_vector.south
		bbv_west = bbox_vector.west
		bbv_east = bbox_vector.east
		# close vector
		vtopo.close()	
		grass.message( "north: %s south: %s west: %s east: %s" % (bbv_north, bbv_south, bbv_west, bbv_east))
		
    ######
    # print bbox of vector layer geometries
    ###### 
    if print_bbox_vector_geometries :
		# open vector
		vtopo = VectorTopo(vector)
		vtopo.open(mode = 'r')
		# loop thru vector geometries		
		for i in range(1, vcats_max_plus):
				# get vector geometries area info
				vect_geom_area = Area(v_id = i, c_mapinfo = vtopo.c_mapinfo)
				# get vector geometries bbox info				
				vect_geom_bb = vect_geom_area.bbox()
				# bbox north, south, west, east
				bb_north = vect_geom_bb.north
				bb_south = vect_geom_bb.south
				bb_west = vect_geom_bb.west
				bb_east = vect_geom_bb.east
				grass.message("cat %s: north: %s south: %s west: %s east: %s" %(i, bb_north, bb_south, bb_west, bb_east))
		# close vector
		vtopo.close()				

    ######
    # export xml files
    ###### 
    if export_cmds :
		# define file with gdal_translate cmds	
		cmd_file = os.path.join( directory, filename )
		# open file
		cf = open(cmd_file, 'wb')
		# open vector
		vtopo = VectorTopo(vector)
		vtopo.open(mode = 'r')
		# loop thru vector geometries		
		for i in range(1, vcats_max_plus):
				# get vector geometries area info
				vect_geom_area = Area(v_id = i, c_mapinfo = vtopo.c_mapinfo)
				# get vector geometries bbox info				
				vect_geom_bb = vect_geom_area.bbox()
				# bbox north, south, west, east
				bb_north = vect_geom_bb.north
				bb_south = vect_geom_bb.south
				bb_west = vect_geom_bb.west
				bb_east = vect_geom_bb.east
				# cast bbox north, south, west, east to integer as GDAL needs inter coordinates
				bb_north_i = int(bb_north)
				bb_south_i = int(bb_south)
				bb_west_i = int(bb_west)
				bb_east_i = int(bb_east)
				# increase bbox north and east +1, decrease bbox west and south -1 to get overlapping tiles
				bb_north_i_plus = bb_north_i + 1
				bb_south_i_plus = bb_south_i - 1
				bb_west_i_plus = bb_west_i - 1
				bb_east_i_plus = bb_east_i + 1				
				# cast to string
				i_str = str(i)
				bb_north_i_plus_str = str(bb_north_i_plus)
				bb_south_i_plus_str = str(bb_south_i_plus)
				bb_west_i_plus_str = str(bb_west_i_plus)
				bb_east_i_plus_str = str(bb_east_i_plus)
				# construct output raster name				
				output_rastername = prefix+'_'+i_str+'_'+bb_west_i_plus_str+'_'+bb_north_i_plus_str+'_'+bb_east_i_plus_str+'_'+bb_south_i_plus_str+'.tif'
				# write gdal_translate cmds
				cf.write("gdal_translate -projwin %s %s %s %s -co TILED=YES -co COMPRESS=LZW -co PREDICTOR=2 %s %s\n" %(bb_west_i_plus_str, bb_north_i_plus_str, bb_east_i_plus_str, bb_south_i_plus_str, inraster, output_rastername))				
				
		# close vector and file
		vtopo.close()
		cf.close()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
