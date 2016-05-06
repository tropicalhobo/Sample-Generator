__author__ = 'G Torres'

import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import random
import os
import sys
from subprocess import call


class RandomSample:

    def __init__(self, f, s_size=500, i_pix=[0, 15], r_path=None, buff_dist=10):

        if os.path.exists(f) is False:
            raise ValueError, "file does not exist"

        # collect image parameters
        self.img_parameters(f)

        # check if raster image is a land cover classification image
        lc_image = self.img_check()
        if lc_image:
            pass
        else:
            print "raster is not a land cover classification image!"
            sys.exit(1)

        self.roads = r_path
        self.buffer_dist = buff_dist
        self.file_name = f
        self.sample_size = s_size
        self.ignore_pix = i_pix

    def img_check(self):
        """Checks if raster image is land classification image"""
        class_cat = self.band.GetCategoryNames()
        if class_cat is None:
            return False
        else:
            return True

    def __str__(self):
        num_cat = len(self.band.GetCategoryNames())
        histogram = self.band.GetHistogram()
        sampling_pixels = 0
        for i in range(num_cat):
            sampling_pixels += histogram[i]
        #color_int = self.band.GetColorInterpretation()
        #color_ent = gdal.GetColorInterpretationName(color_int)
        #pal_name = gdal.GetPaletteInterpretationName(color_int)
        #color_tab = self.band.GetColorTable()
        return '\nclassification image has %d classes with a total of %d pixels' % (num_cat, sampling_pixels)

    def buffer_road(self):
        import ogr

        b_dist = self.buffer_dist
        road_ds = ogr.Open(self.roads, 0)
        drv = road_ds.GetDriver()

        road_lyr = road_ds.GetLayer(0)
        road_count = road_lyr.GetFeatureCount()
        print 'There are %d features in the shp file' % road_count
        # loop through all features and buffer
        for i in range(road_count):
            road = road_lyr.GetFeature(i)
            road_geom = road.GetGeometryRef()
            geom_type = road_geom.GetGeometryName()
            if 'LINESTRING' in geom_type:  # checks if
                print geom_type
            elif 'MULTILINESTRING' in geom_type:
                print geom_type
            else:
                print '\nshapefile not a linestring!'
        # TODO: implement geometry type check. abort operation if type not line
            #road_buff = road_geom.Buffer(b_dist)  # buffer road feature

        return

    def clip_dataset(self):
        pass

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

        return

    def get_samples(self):
        """Generates a random sample of coordinates within the desired map classes.
        Returns list type with tuple elements of pixel coordinates."""
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
        bn = os.path.basename(self.file_name)
        t = time.localtime()
        time_stamp = str(t[0]) + str(t[1]) + str(t[2]) + str(t[3]) \
              + str(t[4]) + str(t[5]) + str(t[6])
        new = time_stamp + "_" + bn + "_random_samples" + ".csv"

        return new

    def save_to_csv(self):
        """Saves samples to a csv file."""
        import csv

        with open(self.new_csv, 'wb') as csvfile:
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

    def __init__(self, f, i_pix=[0, 15], prop=5):
        RandomSample.__init__(self, f, i_pix)

        if prop <= 100:
            pass
        else:
            raise ValueError, "proportion must be <= 100"

    def get_samples(self):
        """Collect random coordinates within classes according to user-specified
        proportion."""
        band_hist = self.band.GetHistogram()
        band_max = self.band.GetMaximum()
        band_min = self.band.GetMinimum()
        #stat = self.band.GetStatistics(0, 0)

        class_prop = {}
        self.rand_coord = {}

        # iterate each class value to perform stratified sampling
        for pix_val in range(int(band_min), int(band_max)):
            if pix_val in self.ignore_pix:
                pass
            else:
                class_prop[pix_val] = int((band_hist[pix_val]*  # compute class proportion for sampling
                                           self.class_proportion)/100)
                self.data = self.band.ReadAsArray(0, 0, self.cols, self.rows)
                pix_class = np.in1d(self.data, pix_val).reshape(self.data.shape)  # select pixels from image array
                pix_loc = np.where(pix_class)  # collect the pixel coordinates of current pixel value
                pix_coord = random.sample(zip(pix_loc[0], pix_loc[1]),  # collect pixel coordinates randomly using
                                          class_prop[pix_val])          # class proportion
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
    road = "C:\Users\G Torres\Desktop\GmE205FinalProject\\bulacan_roads.shp"

    random_sample = RandomSample(test_lc, r_path=road, buff_dist=10)
    #strat_sample = StratSample(test_lc, i_pix=[0,15], prop=1)

    print random_sample
    print random_sample.buffer_road()


if __name__ == "__main__":
    main()