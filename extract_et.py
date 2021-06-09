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
        extract_et(infile, outfile)
    pass


def in2outfiles(infiles, outdir):
    outfiles = []
    for infile in infiles:
        inbase = os.path.basename(infile)
        outfiles.append(os.path.join(outdir, 'et.' + inbase))
    return outfiles


def extract_et(infile, outfile):
    with nc.Dataset(infile, 'r') as fi,\
            nc.Dataset(outfile, 'w') as fo:
        # global attributes
        fo.Conventions = 'CF-1.8'
        fo.title = 'NLDAS-NoahMP evapotranspiration and its components'
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
        fo.createVariable('ET', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['ET'].units = 'kg m-2 s-1'
        fo.variables['ET'].standard_name = 'water_evapotranspiration_flux'
        fo.variables['ET'].long_name = 'evapotranspiration'
        fo.createVariable('ETRAN', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['ETRAN'].units = 'kg m-2 s-1'
        fo.variables['ETRAN'].standard_name = 'transpiration_flux'
        fo.variables['ETRAN'].long_name = 'transpiration'
        fo.createVariable('ECAN', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['ECAN'].units = 'kg m-2 s-1'
        fo.variables['ECAN'].standard_name = 'water_evaporation_flux_from_canopy'
        fo.variables['ECAN'].long_name = 'canopy evaporation'
        fo.createVariable('EDIR', 'f4', ('time', 'lat', 'lon'),
                          fill_value=float('nan'), zlib=True, complevel=6)
        fo.variables['EDIR'].units = 'kg m-2 s-1'
        fo.variables['EDIR'].standard_name = 'water_evaporation_flux_from_soil'
        fo.variables['EDIR'].long_name = 'soil evaporation'
        # write data
        for itim, tim in enumerate(fi.variables['time'][:]):
            fo.variables['time'][itim] = tim
            ec = fi.variables['ECAN'][itim, :, :]
            eg = fi.variables['EDIR'][itim, :, :]
            ev = fi.variables['ETRAN'][itim, :, :]
            et = ec + eg + ev
            fo.variables['ECAN'][itim, :, :] = ec
            fo.variables['EDIR'][itim, :, :] = eg
            fo.variables['ETRAN'][itim, :, :] = ev
            fo.variables['ET'][itim, :, :] = et
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='extract evapotranspiration and its omponents.')
    parser.add_argument('indir', type=str,
                        help='input directory')
    parser.add_argument('outdir', type=str,
                        help='output directory')
    args = parser.parse_args()
    main(args.indir, args.outdir)
