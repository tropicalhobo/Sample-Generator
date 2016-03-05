import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import os
import random

__author__ = 'G Torres'


gdal.AllRegister()


class RandomSample:

    def __init__(self, f):
        self.ignore_pix = None
        self.raster = self.open_raster(f)
        self.image_attributes = self.get_attributes(self.raster)

    def open_raster(self, fn):
        ds = gdal.Open(fn, GA_ReadOnly)
        return ds

    def get_dimensions(self, raster):
        cols = raster.RasterXSize
        rows = raster.RasterYSize
        return cols, rows

    def get_geotransform(self, rstr):
        geotrans = rstr.GetGeoTransform()
        return geotrans

    def get_projection(self, rstr):
        projection = rstr.GetProjection()
        return projection

    def mask_image(self, rstr, ipix, dim):
        ignore_pixel = ipix
        band = rstr.GetRasterBand(1)
        data = band.ReadAsArray(0, 0, dim[0], dim[1])
        return data




def main():
    #import csv
    print os.getcwd()

    tst_landcover = "TST_LC.tif"

    lc_raster = RandomSample(tst_landcover)

    print lc_raster

    """
    print 'Pixel Coordinates: Map Coordinates, Pixel Value'

    count = 1
    with open('test_sample6.csv', 'wb') as csvfile:
        sample_writer = csv.writer(csvfile, delimiter=',')
        sample_writer.writerow(['Geog_x', 'Geog_y',
                                'Proj_x', 'Proj_y',
                                'Pix_Val'])

        for i in lc_raster:
            sample_writer.writerow([lc_raster[i][1][0],  # longitude
                                   lc_raster[i][1][1],  # latitude
                                   lc_raster[i][0][0],  # projected x coord
                                   lc_raster[i][0][1],  # projected y coord
                                   lc_raster[i][2]])  # pixel value

            print count, '.', i, ':', lc_raster[i][1], \
                ',', lc_raster[i][0], ',', lc_raster[i][2]
            count += 1
    """
if __name__ == "__main__":
    main()