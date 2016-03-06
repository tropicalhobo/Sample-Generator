# Sample-Generator
Implementation of sampling schemes for ground-truth points from land classification maps.

OBJECTIVE: To derive thematic map ground-truth point samples from land cover maps using random & random stratified sampling

Packages used:
GDAL, OGR, pyproj, random

Inputs: 
Road shp file from open street map
Land cover map in .tif format or ENVI format
DEM
User input of number of points to be ground truth per class (in absolute numbers or percentage per class)

Outputs:
Txt file containing areas of each class and the total number of pixels
Shp file containing land cover information
.csv file with coordinates of sample points and land cover info as an attribute of each point
