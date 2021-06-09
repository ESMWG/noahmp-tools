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
        extract_rad(infile, outfile)
    return


def in2outfiles(infiles, outdir):
    outfiles = []
    for infile in infiles:
        inbase = os.path.basename(infile)
        outfiles.append(os.path.join(outdir, 'rad.' + inbase))
    return outfiles


def extract_rad(infile, outfile):
    with nc.Dataset(infile, 'r') as fi,\
         nc.Dataset(outfile, 'w') as fo:
        # dimensions
        tim = fi.variables['time'][:]
        lat = fi.variables['south_north'][:]
        lon = fi.variables['west_east'][:]
        nlat = len(fi.dimensions['south_north'])
        nlon = len(fi.dimensions['west_east'])
        fo.createDimension('time', None)
        fo.createDimension('lat', nlat)
        fo.createDimension('lon', nlon)
        # coordinates
        fo.createVariable('time', 'f8', ('time',), zlib=True)
        fo.variables['time'].units = fi.variables['time'].units
        fo.variables['time'].standard_name = 'time'
        fo.createVariable('lat', 'f8', ('lat',), zlib=True)
        fo.variables['lat'].units = fi.variables['south_north'].units
        fo.variables['lat'].standard_name = fi.variables['south_north'].standard_name
        fo.createVariable('lon', 'f8', ('lon',), zlib=True)
        fo.variables['lon'].units = fi.variables['west_east'].units
        fo.variables['lon'].standard_name = fi.variables['west_east'].standard_name
        fo.variables['lat'][:] = lat
        fo.variables['lon'][:] = lon
        # model values
        fo.createVariable('SWU', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True)
        fo.variables['SWU'].units = 'W m-2'
        fo.variables['SWU'].long_name = 'upward_solar_radiation'
        fo.createVariable('LWU', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True)
        fo.variables['LWU'].units = 'W m-2'
        fo.variables['LWU'].long_name = 'upward_longwave_radiation'
        # write data
        for itim, tim in enumerate(fi.variables['time'][:]):
            fo.variables['time'][itim] = tim
            swd = fi.variables['SWFORC'][itim,:,:]
            swa = fi.variables['FSA'][itim,:,:]
            swu = swd - swa
            fo.variables['SWU'][itim,:,:] = swu
            lwd = fi.variables['LWFORC'][itim,:,:]
            lwa = -fi.variables['FIRA'][itim,:,:]
            lwu = lwd - lwa
            fo.variables['LWU'][itim,:,:] = lwu
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='extract upward shortwave and longwave radiation.')
    parser.add_argument('indir', type=str,
                        help='input directory')
    parser.add_argument('outdir', type=str,
                        help='output directory')
    args = parser.parse_args()
    main(args.indir, args.outdir)
