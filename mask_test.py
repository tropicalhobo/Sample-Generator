__author__ = 'G Torres'

import gdal, ogr
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
    mask = np.in1d(data, ignore_pix).reshape(data.shape)
    non_mask = np.where(mask == False)
    mdata = ma.array(data,mask=mask)
    nonmask_ind = ma.where(mdata>0)
    rand_ind = np.choice(np.arange(nonmask_ind[0].size),500)


    # random sampling of pixels
    choice = 500

    #random_col = np.random.choice(non_mask[0],choice)
    #random_row = np.random.choice(non_mask[1],choice)
    #random_pix = data[np.ix_(random_col, random_row)]


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

    return nonmask_ind[0].size, nonmask_ind[1].size


def main():
    import csv
    print os.getcwd()

    tst_landcover = "TST_LC.tif"

    lc_raster = pixel_counter(tst_landcover)

    print lc_raster

if __name__ == "__main__":
    main()