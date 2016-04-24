__author__ = 'G Torres'

import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import random
import os


class RandomSample:

    def __init__(self, f, s_size=500, i_pix=[0, 15]):

        if os.path.exists(f) is False:
            raise ValueError, "file does not exist"

        self.file_name = f
        self.sample_size = s_size
        self.ignore_pix = i_pix

        self.img_parameters(f)

        #self.get_samples()
        #self.pix_to_map()

    def img_parameters(self, f):
        gdal.AllRegister()
        self.raster = gdal.Open(f, GA_ReadOnly)
        self.cols = self.raster.RasterXSize
        self.rows = self.raster.RasterYSize
        self.projection = self.raster.GetProjection()
        self.geotrans = self.raster.GetGeoTransform()
        self.band = self.raster.GetRasterBand(1)

        return

    def get_samples(self):
        """Generates a random sample of coordinates within the desired map classes."""
        ignore_pixel = self.ignore_pix
        self.data = self.band.ReadAsArray(0, 0, self.cols, self.rows)
        mask = np.in1d(self.data, ignore_pixel).reshape(self.data.shape)  # returns boolean of ignored values
        masked_data = ma.array(self.data, mask=mask)  # masks the image-array
        nonmask_ind = ma.where(masked_data > 0)  # returns the indices of non-masked elements

        self.rand_coord = random.sample(zip(nonmask_ind[0],
                                       nonmask_ind[1]),
                                   self.sample_size)

        return

    def pix_to_map(self):
        """Converts the sample of geographic coordinates to utm projected map coordinates."""
        coord_samples = self.rand_coord
        topleft_x = self.geotrans[0]
        topleft_y = self.geotrans[3]
        pix_width = self.geotrans[1]
        pix_height = self.geotrans[5]*-1

        self.samples = {}

        from pyproj import Proj, transform

        wgs84 = Proj(proj='latlong', ellps='WGS84')
        utm51n = Proj(proj='utm', zone=51, ellps='WGS84')

        for coord in coord_samples:
            x_coord = topleft_x + coord[0]*pix_width
            y_coord = topleft_y - coord[1]*pix_height

            x_geo, y_geo = transform(utm51n, wgs84, x_coord, y_coord)

            self.samples[coord] = (x_coord, y_coord), (x_geo, y_geo), self.data[coord[0], coord[1]]

        return

    def new_csv(self):
        """Creates a new csv file with current date and time as suffix"""
        import time
        bn = os.path.basename(self.file_name)
        t = time.localtime()
        time_stamp = str(t[0]) + str(t[1]) + str(t[2]) + str(t[3]) \
              + str(t[4]) + str(t[5]) + str(t[6])
        new = time_stamp + "_" + bn + "_random_samples" + ".csv"

        return new

    def save_to_csv(self):
        """Saves samples to a csv file."""
        import csv

        with open(self.new_csv(), 'wb') as csvfile:
            sample_writer = csv.writer(csvfile, delimiter=',')
            sample_writer.writerow(['id', 'geog_x', 'geog_y',
                                    'proj_x', 'proj_y',
                                    'pix_val'])

            sample_id = 1
            for i in self.samples:

                sample_writer.writerow([sample_id,  # id number
                                       self.samples[i][1][0],  # longitude
                                       self.samples[i][1][1],  # latitude
                                       self.samples[i][0][0],  # projected x coord
                                       self.samples[i][0][1],  # projected y coord
                                       self.samples[i][2]])  # pixel value

                sample_id += 1


class StratSample(RandomSample):

    def __init__(self, f, i_pix=[1, 15], prop=10):
        RandomSample.__init__(self, f, i_pix)

        if prop <= 100:
            pass
        else:
            raise ValueError, "proportion must be <= 100"

        self.class_proportion = prop

    def stratify_samples(self):
        band_hist = self.band.GetHistogram()
        band_max = self.band.GetMaximum()
        band_min = self.band.GetMinimum()
        #stat = self.band.GetStatistics(0, 0)

        class_prop = {}
        self.strat_samples = {}

        for pix_val in range(int(band_min), int(band_max)):
            if pix_val in self.ignore_pix:
                pass
            else:
                class_prop[pix_val] = band_hist[pix_val], int((band_hist[pix_val]*
                                                              self.class_proportion)/100)
                self.data = self.band.ReadAsArray(0, 0, self.cols, self.rows)
                pix_class = np.in1d(self.data, pix_val).reshape(self.data.shape)
                pix_loc = np.where(pix_class)
                pix_coord = random.sample(zip(pix_loc[0], pix_loc[1]),
                                          class_prop[pix_val][1])
                self.strat_samples[pix_val] = pix_coord

        return self.strat_samples

    def new_csv(self):
        """Creates a new csv file with current date and time as suffix"""
        import time
        bn = os.path.basename(self.file_name)
        t = time.localtime()
        time_stamp = str(t[0]) + str(t[1]) + str(t[2]) + str(t[3]) \
                     + str(t[4]) + str(t[5]) + str(t[6])
        new = time_stamp + "_" + bn + "_strat_samples" + ".csv"

        return new

    def save_to_csv(self):
        """Saves samples to a csv file."""
        import csv

        with open(self.new_csv(), 'wb') as csvfile:
            sample_writer = csv.writer(csvfile, delimiter=',')
            sample_writer.writerow(['id', 'geog_x', 'geog_y',
                                    'proj_x', 'proj_y',
                                    'pix_val'])

            sample_id = 1
            for i in self.strat_samples:
                sample_writer.writerow([sample_id,  # id number
                                        self.strat_samples[i][1][0],  # longitude
                                        self.strat_samples[i][1][1],  # latitude
                                        self.strat_samples[i][0][0],  # projected x coord
                                        self.strat_samples[i][0][1],  # projected y coord
                                        self.strat_samples[i][2]])  # pixel value

                sample_id += 1


def main():

    test_lc = "C:\Users\G Torres\Desktop\GmE205FinalProject\\test_lc"

    #lc = RandomSample(test_lc)

    #lc.save_to_csv()

    lc2 = StratSample(test_lc)

    class_prop = lc2.stratify_samples()

    for i in class_prop:
        print i, class_prop[i]


if __name__ == "__main__":
    main()