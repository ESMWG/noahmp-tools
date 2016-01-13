#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import os.path
import shutil
import datetime
import subprocess
import tempfile
import numpy as np
import netCDF4 as nc
import argparse

MVMIN = -1.0e+10
FIXEDVARS = set(['time', 'south_north', 'west_east', 'lat', 'lon', 'xlat', 'xlon'])

np.seterr(invalid='ignore')

def main(wrfinput, files):
    with nc.Dataset(wrfinput, 'r') as f:
        if f.MAP_PROJ == 6:
            appendlatlon = True
            lon2d = np.squeeze(f.variables['XLONG'][:,:])
            lat2d = np.squeeze(f.variables['XLAT'][:,:])
            lon = lon2d[0,:]
            lat = lat2d[:,0]
        else:
            appendlatlon = False
    for f in files:
        print(f)
        cdir = os.path.dirname(f)
        renamelon = False
        renamelat = False
        renametim = False
        deletetim = False
        with nc.Dataset(f, 'r') as ncf:
            if 'west_east' in ncf.dimensions:
                renamelon = True
            if 'south_north' in ncf.dimensions:
                renamelat = True
            if 'Time' in ncf.dimensions:
                renametim = True
            if 'Times' in ncf.variables:
                deletetim = True
        if renamelon:
            subprocess.run(['ncrename', '-Oh', '-d', 'west_east,lon', f])
        if renamelat:
            subprocess.run(['ncrename', '-Oh', '-d', 'south_north,lat', f])
        if renametim:
            subprocess.run(['ncrename', '-Oh', '-d', 'Time,time', f])

        with tempfile.NamedTemporaryFile(prefix=cdir, suffix='.nc') as tmp:
            subprocess.run(
                ['ncpdq', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                 '-a', 'time,snow_layers,soil_layers_stag,lat,lon', f, tmp.name])
            shutil.copyfile(tmp.name, f)

        with nc.Dataset(f, 'r+') as ncf:
            mv = ncf.missing_value
            for var in ncf.variables:
                if var.lower() in FIXEDVARS:
                    continue
                if np.issubdtype(ncf.variables[var].dtype, np.float):
                    v = ncf.variables[var][:]
                    ncf.variables[var][:] = np.where(np.logical_or(v==mv, v<=MVMIN), 
                                                     np.nan, v)
            if ('lat' not in ncf.variables) and appendlatlon:
                ncf.createVariable('lat', 'f4', ('lat',), zlib=True, complevel=6)
                ncf.variables['lat'].units = 'degree_north'
                ncf.variables['lat'].standard_name = 'latitude'
                ncf.variables['lat'][:] = lat
            if ('lon' not in ncf.variables) and appendlatlon:
                ncf.createVariable('lon', 'f4', ('lon',), zlib=True, complevel=6)
                ncf.variables['lon'].units = 'degree_east'
                ncf.variables['lon'].standard_name = 'longitude'
                ncf.variables['lon'][:] = lon
            if ('time' not in ncf.variables) and ('Times' in ncf.variables):
                ncf.createVariable('time', 'f8', ('time',), zlib=True, complevel=6)
                ncf.variables['time'].units = 'hours since 1900-01-01'.encode('ascii')
                ncf.variables['time'].calendar = 'standard'.encode('ascii')
                dts = [datetime.datetime.strptime(str(x, 'ascii'), '%Y-%m-%d_%H:%M:%S')
                        for x in nc.chartostring(ncf.variables['Times'][:])]
                ncf.variables['time'][:] = nc.date2num(dts, 'hours since 1900-01-01')
        if deletetim:
            with tempfile.NamedTemporaryFile(prefix=cdir, suffix='.nc') as tmp:
                subprocess.run(['ncks', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                                '-x', '-v', 'Times', f, tmp.name])
                shutil.copyfile(tmp.name, f)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('wrfinput')
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    main(args.wrfinput, args.files)
