__author__ = 'G Torres'

import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import os
import random


class RandomSample:

    def __init__(self, f, s_size=500, i_pix=[0, 15]):
        self.sample_size = s_size
        self.ignore_pix = i_pix
        self.raster = self.open_raster(f)
        self.dim = self.img_dimensions()
        self.geotrans = self.img_geotransform()
        self.proj = self.img_projection()

    def open_raster(self, f):
        gdal.AllRegister()
        ds = gdal.Open(f, GA_ReadOnly)
        if os.path.exists(f) == None:
            return "File does not exist."
        else:
            return ds

    def img_dimensions(self):
        cols = self.raster.RasterXSize
        rows = self.raster.RasterYSize
        return cols, rows

    def img_geotransform(self):
        geotrans = self.raster.GetGeoTransform()
        return geotrans

    def img_projection(self):
        projection = self.raster.GetProjection()
        return projection

    def sampler(self):
        """Generates a random sample of coordinates within the desired map classes."""
        ignore_pixel = self.ignore_pix
        band = self.raster.GetRasterBand(1)
        data = band.ReadAsArray(0, 0, self.dim[0], self.dim[1])
        mask = np.in1d(data, ignore_pixel).reshape(data.shape)  # returns boolean of ignored values
        mdata = ma.array(data, mask=mask)  # masks the image-array
        nonmask_ind = ma.where(mdata > 0)  # returns the indices of non-masked elements

        rand_coord = random.sample(zip(nonmask_ind[0],
                                       nonmask_ind[1]),
                                   self.sample_size)

        yield rand_coord

    def pix_to_map(self):
        """Converts the sample of geographic coordinates to projected map coordinates."""
        sample = self.sampler()
        topleft_x = self.geotrans[0]
        topleft_y = self.geotrans[3]
        pix_width = self.geotrans[1]
        pix_height = self.geotrans[5]*-1

        map_val = {}

        from pyproj import Proj, transform

        wgs84 = Proj(proj='latlong', ellps='WGS84')
        utm51n = Proj(proj='utm', zone=51, ellps='WGS84')

        for coord in self.sample:
            x_coord = topleft_x + coord[0]*pix_width
            y_coord = topleft_y - coord[1]*pix_height

            x_geo, y_geo = transform(utmn, wgs84, x_coord, y_coord)

            map_val[coord] = (x_coord, y_coord), (x_geo, y_geo), sample[
                coord[0], coord[1]]

        yield map_val




def main():
    #import csv
    #print os.getcwd()

    tst_landcover = "C:\Users\G Torres\Desktop\GmE205FinalProject\\test_lc"

    lc = RandomSample(tst_landcover)

    print lc.dim, '\n', lc.sampler()

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