#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import glob
import argparse
import netCDF4 as nc


def main(indir, outdir):
    infiles = sorted(glob.glob(os.path.join(indir, '*.nc')))
    outfiles = in2outfiles(infiles, outdir)
    for infile, outfile in zip(infiles, outfiles):
        print(infile + ' -> ' + outfile, flush=True)
        extract_runoff(infile, outfile)
    pass


def in2outfiles(infiles, outdir):
    outfiles = []
    for infile in infiles:
        inbase = os.path.basename(infile)
        outfiles.append(os.path.join(outdir, 'run.' + inbase))
    return outfiles


def extract_runoff(infile, outfile):
    with nc.Dataset(infile, 'r') as fi,\
            nc.Dataset(outfile, 'w') as fo:
        # global attributes
        fo.Conventions = 'CF-1.8'
        fo.title = 'NLDAS-NoahMP runoff and its components'
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
        fo.createDimension('time', None)
        fo.createDimension('lat', nlat)
        fo.createDimension('lon', nlon)
        # coordinates
        fo.createVariable('time', 'f8', ('time',), zlib=True, complevel=6)
        fo.variables['time'].units = fi.variables['time'].units
        fo.variables['time'].standard_name = 'time'
        fo.variables['time'].axis = 'T'
        fo.createVariable('lat', 'f8', ('lat',), zlib=True, complevel=6)
        fo.variables['lat'].units = fi.variables['south_north'].units
        fo.variables['lat'].standard_name = fi.variables['south_north'].standard_name
        fo.variables['lat'].axis = 'Y'
        fo.createVariable('lon', 'f8', ('lon',), zlib=True, complevel=6)
        fo.variables['lon'].units = fi.variables['west_east'].units
        fo.variables['lon'].standard_name = fi.variables['west_east'].standard_name
        fo.variables['lon'].axis = 'X'
        fo.variables['lat'][:] = lat
        fo.variables['lon'][:] = lon
        # model values
        fo.createVariable('RUNOFF', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['RUNOFF'].units = 'kg m-2 s-1'
        fo.variables['RUNOFF'].standard_name = 'runoff_flux'
        fo.variables['RUNOFF'].long_name = 'runoff'
        fo.createVariable('SFCRNOFF', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['SFCRNOFF'].units = 'kg m-2 s-1'
        fo.variables['SFCRNOFF'].standard_name = 'surface_runoff_flux'
        fo.variables['SFCRNOFF'].long_name = 'surface runoff'
        fo.createVariable('UGDRNOFF', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['UGDRNOFF'].units = 'kg m-2 s-1'
        fo.variables['UGDRNOFF'].standard_name = 'subsurface_runoff_flux'
        fo.variables['UGDRNOFF'].long_name = 'subsurface runoff'
        # write data
        for itim, tim in enumerate(fi.variables['time'][:]):
            fo.variables['time'][itim] = tim
            runs = fi.variables['SFCRNOFF'][itim, :, :]
            rung = fi.variables['UGDRNOFF'][itim, :, :]
            run = runs + rung
            fo.variables['SFCRNOFF'][itim, :, :] = runs
            fo.variables['UGDRNOFF'][itim, :, :] = rung
            fo.variables['RUNOFF'][itim, :, :] = run
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='extract runoff components.')
    parser.add_argument('indir', type=str,
                        help='input directory')
    parser.add_argument('outdir', type=str,
                        help='output directory')
    args = parser.parse_args()
    main(args.indir, args.outdir)
