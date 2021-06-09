#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import glob
import argparse
import numpy as np
import netCDF4 as nc


def main(indir, outdir):
    infiles = sorted(glob.glob(os.path.join(indir, '*.nc')))
    outfiles = in2outfiles(infiles, outdir)
    for infile, outfile in zip(infiles, outfiles):
        print(infile + ' -> ' + outfile, flush=True)
        extract_tws(infile, outfile)
    pass


def in2outfiles(infiles, outdir):
    outfiles = []
    for infile in infiles:
        inbase = os.path.basename(infile)
        outfiles.append(os.path.join(outdir, 'tws.' + inbase))
    return outfiles


def extract_tws(infile, outfile):
    with nc.Dataset(infile, 'r') as fi, \
            nc.Dataset(outfile, 'w') as fo:
        # global attributes
        fo.Conventions = 'CF-1.8'
        fo.title = 'NLDAS-NoahMP terrestrial water storage and its components'
        fo.institution = 'Institute of Atmospheric Physics, Chinese Academy of Sciences'
        fo.source = 'Noah-MP v3.6 driven by NLDAS-2'
        fo.references = ''
        fo.comment = ''
        # dimensions
        tim = fi.variables['time'][:]
        lat = fi.variables['south_north'][:]
        lon = fi.variables['west_east'][:]
        nlat = len(fi.dimensions['south_north'])
        nlon = len(fi.dimensions['west_east'])
        depth = np.array([0.05, 0.25, 0.7, 1.5, 0.5, 1.0])
        depth_bnds = np.transpose(np.array([[0.0, 0.1, 0.4, 1.0, 0.0, 0.0],
                                            [0.1, 0.4, 1.0, 2.0, 1.0, 2.0]]))
        ndepth = len(depth)
        fo.createDimension('time', None)
        fo.createDimension('depth', ndepth)
        fo.createDimension('lat', nlat)
        fo.createDimension('lon', nlon)
        fo.createDimension('bnd', 2)
        # coordinates
        fo.createVariable('time', 'f8', ('time',), zlib=True, complevel=6)
        fo.variables['time'].units = fi.variables['time'].units
        fo.variables['time'].standard_name = 'time'
        fo.variables['time'].axis = 'T'
        fo.createVariable('depth', 'f4', ('depth',), zlib=True, complevel=6)
        fo.variables['depth'].units = 'm'
        fo.variables['depth'].standard_name = 'depth'
        fo.variables['depth'].positive = 'down'
        fo.variables['depth'].axis = 'Z'
        fo.variables['depth'].bounds = 'depth_bnds'
        fo.createVariable('depth_bnds', 'f4', ('depth', 'bnd'),
                          zlib=True, complevel=6)
        fo.createVariable('lat', 'f8', ('lat',), zlib=True, complevel=6)
        fo.variables['lat'].units = fi.variables['south_north'].units
        fo.variables['lat'].standard_name = fi.variables['south_north'].standard_name
        fo.variables['lat'].axis = 'Y'
        fo.createVariable('lon', 'f8', ('lon',), zlib=True, complevel=6)
        fo.variables['lon'].units = fi.variables['west_east'].units
        fo.variables['lon'].standard_name = fi.variables['west_east'].standard_name
        fo.variables['lon'].axis = 'X'
        fo.variables['depth'][:] = depth
        fo.variables['depth_bnds'][:] = depth_bnds
        fo.variables['lat'][:] = lat
        fo.variables['lon'][:] = lon
        # model values
        fo.createVariable('TWS', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['TWS'].units = 'kg m-2'
        fo.variables['TWS'].standard_name = 'land_water_amount'
        fo.variables['TWS'].long_name = 'terrestrial water storage'
        fo.createVariable('SMC', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['SMC'].units = 'kg m-2'
        fo.variables['SMC'].standard_name = 'mass_content_of_water_in_soil'
        fo.variables['SMC'].long_name = 'soil moisture content'
        fo.createVariable('SNW', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['SNW'].units = 'kg m-2'
        fo.variables['SNW'].standard_name = 'surface_snow_amount'
        fo.variables['SNW'].long_name = 'snow water equivalent'
        fo.createVariable('GW', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['GW'].units = 'kg m-2'
        fo.variables['GW'].long_name = 'groundwater storage'
        fo.createVariable('SOIL_M', 'f4', ('time', 'depth', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['SOIL_M'].units = 'm3 m-3'
        fo.variables['SOIL_M'].standard_name = 'volume_fraction_of_condensed_water_in_soil'
        fo.variables['SOIL_M'].long_name = 'volumetric soil water content'
        fo.createVariable('ZWT', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['ZWT'].units = 'm'
        fo.variables['ZWT'].standard_name = 'water_table_depth'
        fo.variables['ZWT'].long_name = 'water table depth'
        # write data
        for itim, tim in enumerate(fi.variables['time'][:]):
            fo.variables['time'][itim] = tim
            sm = fi.variables['SOIL_M'][itim, :, :, :]
            sm1m = np.average(sm, axis=0, weights=[0.1, 0.3, 0.6, 0.0])
            sm2m = np.average(sm, axis=0, weights=[0.05, 0.15, 0.3, 0.5])
            smc = sm2m * 2000.0
            snw = fi.variables['SNEQV'][itim, :, :]
            gw = fi.variables['WA'][itim, :, :]
            zwt = fi.variables['ZWT'][itim, :, :, ]
            tws = smc + gw + snw
            fo.variables['TWS'][itim, :, :] = tws
            fo.variables['SMC'][itim, :, :] = smc
            fo.variables['SNW'][itim, :, :] = snw
            fo.variables['GW'][itim, :, :] = gw
            fo.variables['SOIL_M'][itim, 0:4, :, :] = sm
            fo.variables['SOIL_M'][itim, 4, :, :] = sm1m
            fo.variables['SOIL_M'][itim, 5, :, :] = sm2m
            fo.variables['ZWT'][itim, :, :] = zwt
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='extract terrestrial water storage and its components.')
    parser.add_argument('indir', type=str,
                        help='input directory')
    parser.add_argument('outdir', type=str,
                        help='output directory')
    args = parser.parse_args()
    main(args.indir, args.outdir)
