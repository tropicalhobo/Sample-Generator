import gdal
from gdalconst import *
import numpy as np
import numpy.ma as ma
import os, random

__author__ = 'G Torres'


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

    # get minimum and maximum of image to create bins
    # band_min = band.GetMinimum()
    # band_max = band.GetMaximum()
    band_hist = band.GetHistogram()

    # pixel counter
    data = band.ReadAsArray(0, 0,
                            cols, rows)

    # land class pixel count and area computation
    lclass_count = {}
    lclass_area = {}

    cnt = 1
    for i in band_hist[1:16]:
        lclass_count[cnt] = i
        lclass_area[cnt] = i*pix_width*pix_height
        cnt += 1

    # classified pixels total area computation
    total_cl_area = 0
    for i in lclass_area:
        total_cl_area += lclass_area[i]

    # proportion computation
    class_proportion = {}
    for j in lclass_area:
        class_proportion[j] = lclass_area[j]/total_cl_area*100

    # return class_proportion

    # mask array to mask out cloud, cloud shadow and 0 values
    ignore_pix = [4, 5, 6, 15]
    mask = np.in1d(data, ignore_pix).reshape(data.shape)  # returns boolean of ignored values
    mdata = ma.array(data,mask=mask)  # masks the image-array
    nonmask_ind = ma.where(mdata>0)  # returns the indices of non-masked elements

    # random selection of indices of non-masked elements
    sample_size = 500
    rand_coord = random.sample(zip(nonmask_ind[0],
                                   nonmask_ind[1]),
                               sample_size)

    # convert pixel coordinate to map coordinates TODO: avoid unwanted pixel values
    map_val = {}

    from pyproj import Proj, transform

    wgs84 = Proj(proj='latlong', ellps='WGS84')
    utm51n = Proj(proj='utm', zone=51, ellps='WGS84')

    for coord in rand_coord:
        x_coord = geo_trans[0]+coord[0]*pix_width  # left to right
        y_coord = geo_trans[3]-coord[1]*pix_height  # top to bottom

        # convert map coordinates to geographic coordinates
        x_geo, y_geo = transform(utm51n, wgs84, x_coord, y_coord)
        map_val[coord] = (x_coord, y_coord), (x_geo, y_geo), data[coord[0], coord[1]]

    return map_val

    # memory clean-up


def main():
    import csv
    print os.getcwd()

    tst_landcover = "TST_LC.tif"

    lc_raster = pixel_counter(tst_landcover)

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

if __name__ == "__main__":
    main()