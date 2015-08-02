#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# convert Princeton Meteorological Forcing Dataset from NetCDF format
# to WPS intermediate file format.

# author: Hui ZHENG
# email: woolf1988@qq.com

import os
import os.path
import struct
import argparse
import dateutil.parser
import numpy as np
import netCDF4 as nc

def wps_write_latlon_field(f,
                           hdate, xfcst, map_src,
                           field, units, desc,
                           xlvl, nx, ny,
                           startloc,
                           startlat, startlon,
                           deltalat, deltalon,
                           is_wind_grid_rel, data):
    version = 5
    iproj = 0
    earth_radius = 6371.229004

    recsize = struct.calcsize('>i')
    f.write(struct.pack('>I', recsize))
    f.write(struct.pack('>i', version))
    f.write(struct.pack('>I', recsize))

    recsize = struct.calcsize('>24s f 32s 9s 25s 46s f i i i')
    f.write(struct.pack('>I', recsize))
    f.write(struct.pack('>24s', hdate.strftime('%Y:%m:%d_%H:%M:%S').encode('ascii')))
    f.write(struct.pack('>f', xfcst))
    f.write(struct.pack('>32s', map_src.ljust(32, ' ').encode('ascii')))
    f.write(struct.pack('>9s', field.ljust(9, ' ').encode('ascii')))
    f.write(struct.pack('>25s', units.ljust(25, ' ').encode('ascii')))
    f.write(struct.pack('>46s', desc.ljust(46, ' ').encode('ascii')))
    f.write(struct.pack('>f', xlvl))
    f.write(struct.pack('>i', nx))
    f.write(struct.pack('>i', ny))
    f.write(struct.pack('>i', iproj))
    f.write(struct.pack('>I', recsize))

    recsize = struct.calcsize('>8s f f f f f')
    f.write(struct.pack('>I', recsize))
    f.write(struct.pack('>8s', startloc.ljust(8, ' ').encode('ascii')))
    f.write(struct.pack('>ff', startlat, startlon))
    f.write(struct.pack('>ff', deltalat, deltalon))
    f.write(struct.pack('>f', earth_radius))
    f.write(struct.pack('>I', recsize))

    recsize = struct.calcsize('>I')
    f.write(struct.pack('>I', recsize))
    f.write(struct.pack('>I', is_wind_grid_rel))
    f.write(struct.pack('>I', recsize))

    bdata = np.array(data, data.dtype.newbyteorder('>'))
    recsize = bdata.nbytes
    f.write(struct.pack('>I', recsize))
    f.write(bdata.tobytes('F'))
    f.write(struct.pack('>I', recsize))

    return

def main(files=None, prefix='FILE', append=False, begtime=None, endtime=None):
    VARS = set(['dswrf', 'dlwrf', 'wind', 'tas', 'shum', 'pres', 'prcp'])

    if files is None:
        return

    # possible outputs
    dates = set()
    for flnm in files:
        if not os.path.isfile(flnm):
            print('Error: no such file ', flnm)
            return
        with nc.Dataset(flnm, 'r') as f:
            dates.update(nc.num2date(f.variables['time'][:],
                                     f.variables['time'].units))
    # delete exsiting intermediate files
    for dd in dates:
        if ((begtime is not None and dd < begtime)
            or (endtime is not None and dd >= endtime)):
            continue
        oflnm = ''.join([prefix, ':', dd.strftime('%Y-%m-%d_%H')])
        if not append and os.path.isfile(oflnm):
            os.remove(oflnm)
    del dates

    # process & write output
    for flnm in files:
        with nc.Dataset(flnm, 'r') as f:
            dates = nc.num2date(f.variables['time'][:],
                                f.variables['time'].units)
            varname = VARS.intersection(set(f.variables.keys())).pop()
            var = f.variables[varname]
            for ii, dd in enumerate(dates):
                if ((begtime is not None and dd < begtime)
                    or (endtime is not None and dd >= endtime)):
                    continue
                oflnm = ''.join([prefix, ':', dd.strftime('%Y-%m-%d_%H')])
                omod = 'ab' if os.path.isfile(oflnm) else 'wb'
                print(oflnm)
                with open(oflnm, omod) as of:
                    xfcst = 0.0
                    map_src = var.source
                    field = varname.upper()
                    units = var.units
                    desc = var.title
                    nx = len(f.dimensions['latitude'])
                    ny = len(f.dimensions['longitude'])
                    startloc = 'SWCORNER'
                    startlat = f.variables['latitude'][0]
                    startlon = f.variables['longitude'][0]
                    deltalat = f.variables['latitude'][1] - f.variables['latitude'][0]
                    deltalon = f.variables['longitude'][1] - f.variables['longitude'][0]
                    is_wind_grid_rel = False
                    for iz in range(len(f.dimensions['z'])):
                        xlvl = f.variables['z'][iz]
                        data = var[ii,iz]
                        wps_write_latlon_field(of,
                                               dd, xfcst, map_src,
                                               field, units, desc,
                                               xlvl, nx, ny,
                                               startloc,
                                               startlat, startlon,
                                               deltalat, deltalon,
                                               is_wind_grid_rel,
                                               data)
    return

if __name__ == '__main__':
    # prefix, append switch
    parser = argparse.ArgumentParser(
        description='Convert Princeton Meteorological Forcing Dataset from NetCDF format to WPS intermediate file format')
    parser.add_argument('file', nargs='+',
                        help='input files')
    parser.add_argument('-p', '--prefix', type=str,
                        help='prefix of resulting intermediate file names',
                        default='FILE')
    parser.add_argument('-a', '--append',
                        help='append data to existing files (other than create new files).',
                        default=False, action='store_true')
    parser.add_argument('-b', '--begtime',
                        help='begin date & time',
                        default=None, type=str)
    parser.add_argument('-e', '--endtime',
                        help='end date & time (exclusive)',
                        default=None, type=str)
    args = parser.parse_args()

    main(files=args.file,
         prefix=args.prefix,
         append=args.append,
         begtime=dateutil.parser.parse(args.begtime) if args.begtime is not None else None,
         endtime=dateutil.parser.parse(args.endtime) if args.endtime is not None else None)
