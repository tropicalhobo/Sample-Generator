__author__ = 'G Torres'

import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import random
import os
import sys


class RandomSample:

    def __init__(self, f, s_size=500, i_pix=[0, 15]):

        if os.path.exists(f) is False:
            raise ValueError, "file does not exist"

        # collect image parameters
        self.img_parameters(f)

        # check if raster image is a land cover classification image
        lc_image = self.img_check()
        if lc_image:
            pass
        else:
            print "\nraster is not a land cover classification image!"
            sys.exit(1)

        self.file_name = f
        self.sample_size = s_size
        self.ignore_pix = i_pix

    def img_check(self):
        """Checks if raster image is land classification image"""
        if self.band.GetCategoryNames() is None:
            return False
        else:
            return True

    def __str__(self):
        num_cat = len(self.class_cat)
        histogram = self.band.GetHistogram()
        sampling_pixels = 0
        for i in range(num_cat):
            sampling_pixels += histogram[i]
        #color_int = self.band.GetColorInterpretation()
        #color_ent = gdal.GetColorInterpretationName(color_int)
        #pal_name = gdal.GetPaletteInterpretationName(color_int)
        #color_tab = self.band.GetColorTable()
        return '\nclassification image has %d classes with a total of %d pixels' % (num_cat, sampling_pixels)

    def img_parameters(self, f):
        """Load image as GDAL object and retrieve image parameters.
        Returns gdal image object and parameters"""
        gdal.AllRegister()
        self.raster = gdal.Open(f, GA_ReadOnly)
        self.cols = self.raster.RasterXSize
        self.rows = self.raster.RasterYSize
        self.projection = self.raster.GetProjection()
        self.geotrans = self.raster.GetGeoTransform()
        self.band = self.raster.GetRasterBand(1)
        self.class_cat = self.band.GetCategoryNames()

        return

    def get_samples(self):
        """Generates a random sample of coordinates within the desired map classes.
        Returns list type with tuple elements of pixel coordinates."""
        print '\ncollecting random coordinates...'
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
        """Converts the sample of geographic coordinates to utm projected map coordinates.
        Returns dict type with tuple elements of geographic and projected coordinates
        with pixel values"""
        print '\nconverting pixel coordinates and collecting pixel values...'
        coord_samples = self.rand_coord
        topleft_x = self.geotrans[0]
        topleft_y = self.geotrans[3]
        pix_width = self.geotrans[1]
        pix_height = self.geotrans[5]

        self.samples = {}

        from pyproj import Proj, transform

        wgs84 = Proj(proj='latlong', ellps='WGS84')
        utm51n = Proj(proj='utm', zone=51, ellps='WGS84')

        for coord in coord_samples:
            x_coord = topleft_x + coord[1]*pix_width
            y_coord = topleft_y + coord[0]*pix_height
            x_geo, y_geo = transform(utm51n, wgs84, x_coord, y_coord)
            self.samples[coord] = (x_coord, y_coord), (x_geo, y_geo), self.data[coord[0], coord[1]]

        return

    def new_csv(self):
        """Creates a new csv file with current date and time as suffix.
        Returns string."""
        import time
        bn = os.path.basename(self.file_name).split('.')[0]
        t = time.localtime()
        time_stamp = str(t[0]) + str(t[1]) + str(t[2]) + str(t[3]) \
              + str(t[4]) + str(t[5]) + str(t[6])
        new = time_stamp + "_" + bn + "_random_samples" + ".csv"

        return new

    def save_to_csv(self):
        """Saves samples to a csv file."""
        import csv
        new_name = self.new_csv()
        print '\nsaving samples to csv...'
        with open(new_name, 'wb') as csvfile:
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

        return


class StratSample(RandomSample):

    def __init__(self, f, s_size=None, i_pix=[0, 15], prop=5):
        RandomSample.__init__(self, f, s_size, i_pix)

        if prop <= 100:
            pass
        else:
            raise ValueError, "proportion must be <= 100"

        self.class_proportion = prop

    def get_samples(self):
        """Collect random coordinates within classes according to user-specified
        proportion."""
        band_hist = self.band.GetHistogram()
        stat = self.band.GetStatistics(0, 1)
        band_max = self.band.GetMaximum()
        band_min = self.band.GetMinimum()
        print band_max
        perc_prop = {}
        abs_prop = self.sample_size
        self.rand_coord = {}

        print "\ncollecting random stratified samples..."
        # iterate each class value to perform stratified sampling
        for pix_val in range(int(band_min), int(band_max)):
            if pix_val in self.ignore_pix:
                pass
            else:
                # sample according to absolute or percentage proportion
                if abs_prop is None:
                    perc_prop[pix_val] = int((band_hist[pix_val]*  # compute class proportion for sampling
                                               self.class_proportion)/100)
                    print '\nusing percentage proportion. %d sample pixels collected with pixel value %d...' % \
                          (perc_prop[pix_val], pix_val)
                    prop = perc_prop[pix_val]
                else:
                    print '\nusing absolute proportion. %d sample pixels collected with pixel value %d...' % \
                          (abs_prop, pix_val)
                    prop = abs_prop
                self.data = self.band.ReadAsArray(0, 0, self.cols, self.rows)
                pix_class = np.in1d(self.data, pix_val).reshape(self.data.shape)  # select pixels from image array
                pix_loc = np.where(pix_class)  # collect the pixel coordinates of current pixel value
                pix_coord = random.sample(zip(pix_loc[0], pix_loc[1]), prop)  # class proportion
                self.rand_coord[pix_val] = pix_coord

        return

    def pix_to_map(self):
        """Converts the sample of geographic coordinates to utm
        projected map coordinates."""

        topleft_x = self.geotrans[0]
        topleft_y = self.geotrans[3]
        pix_width = self.geotrans[1]
        pix_height = self.geotrans[5]

        self.strat_samples = {}

        from pyproj import Proj, transform

        wgs84 = Proj(proj='latlong', ellps='WGS84')
        utm51n = Proj(proj='utm', zone=51, ellps='WGS84')
        print "\nconverting pixel coordinates and collecting pixel values..."
        for strata in self.rand_coord:
            for coord in self.rand_coord[strata]:
                x_coord = topleft_x + coord[1] * pix_width
                y_coord = topleft_y + coord[0] * pix_height
                x_geo, y_geo = transform(utm51n, wgs84, x_coord, y_coord)
                self.strat_samples[coord] = (x_coord, y_coord), (x_geo, y_geo), self.data[coord[0], coord[1]]

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
        new_name = self.new_csv()
        print "\nsaving samples to csv..."
        with open(new_name, 'wb') as f:
            sample_writer = csv.writer(f, delimiter=',')
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

    test_lc = "C:\\Users\\G Torres\\Desktop\\GmE205FinalProject\\GmE205FinalProject\\test_lc"

    random_sample = RandomSample(test_lc)
    strat_sample = StratSample(test_lc, i_pix=[0, 15], prop=10)

    random_sample.get_samples()
    random_sample.pix_to_map()
    #random_sample.save_to_csv()

    strat_sample.get_samples()
    strat_sample.pix_to_map()
    #strat_sample.save_to_csv()

if __name__ == "__main__":
    main()