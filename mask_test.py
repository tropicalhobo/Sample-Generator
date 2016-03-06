__author__ = 'G Torres'

import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import os, random

gdal.AllRegister()

def pixel_counter(fn):
    rs_ds = gdal.Open(fn, GA_ReadOnly)

    if rs_ds is None:
        return 'Could not open ' + fn
        sys.exit(1)

    cols, rows = rs_ds.RasterXSize, rs_ds.RasterYSize
    geo_trans = rs_ds.GetGeoTransform()
    pix_width, pix_height = geo_trans[1], geo_trans[5]*-1
    band = rs_ds.GetRasterBand(1)

    #get minimum and maximum of image to create bins
    #band_min = band.GetMinimum()
    #band_max = band.GetMaximum()
    band_hist = band.GetHistogram()

    #pixel counter
    data = band.ReadAsArray(0,0,
                            cols,rows)

    # mask array to mask out cloud, cloud shadow and 0 values
    ignore_pix = [4,5,6,15]
    mask = np.in1d(data, ignore_pix).reshape(data.shape)  # returns boolean of ignored values
    mdata = ma.array(data,mask=mask)  # masks the image-array
    nonmask_ind = ma.where(mdata>0)  # returns the indices of non-masked elements

    # random selection of indices of non-masked elements
    sample_size = 500
    rand_coord = random.sample(zip(nonmask_ind[0],
                                   nonmask_ind[1]),
                               sample_size)

    #land class pixel count and area computation
    lclass_count = {}
    lclass_area = {}

    cnt = 1
    for i in band_hist[:]:
        lclass_count[cnt] = i
        lclass_area[cnt] = i*pix_width*pix_height
        cnt += 1

    #classified pixels total area computation
    total_cl_area = 0
    for i in lclass_area:
        total_cl_area += lclass_area[i]

    #proportion computation
    class_proportion = {}
    for j in lclass_area:
        class_proportion[j] = lclass_area[j]/total_cl_area*100

    return rand_coord, data


def main():

    print os.getcwd()

    tst_landcover = "TST_LC.tif"

    random_points = pixel_counter(tst_landcover)

    for i in random_points[0]:
        print i, random_points[1][i[0], i[1]]

if __name__ == "__main__":
    main()