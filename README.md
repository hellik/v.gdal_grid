# v.gdal_grid
prototype of calculating bbox of every geometry in a vector layer and writes a GDAL gdal_translate commands to extract tiles matching the vector geometries bbox

the script works as a GRASS GIS addon.

workflow:

- v.mkgrid - to create a vector map of a user-defined grid
- v.gdal_grid -s input=your_vector_grid dir=data prefix=a raster=input.tif file=do_gdaltranslate
- do_gdaltranslate


