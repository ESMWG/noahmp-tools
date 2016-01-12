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

MVMIN = -1e+10
FIXEDVARS = set(['time', 'south_north', 'west_east', 'lat', 'lon', 'xlat', 'xlon'])

np.seterr(invalid='ignore')

def main(files):
    for f in files:
        print(f)
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
        with tempfile.NamedTemporaryFile(suffix='.nc') as tmp:
            subprocess.run(
                ['ncpdq', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                 '-a', 'time,snow_layers,soil_layers_stag,lat,lon', f, tmp.name])
            shutil.copyfile(tmp.name, f)
        if renamelon:
            subprocess.run(['ncrename', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                            '-d', 'west_east,lon', f])
        if renamelat:
            subprocess.run(['ncrename', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                            '-d', 'south_north,lat', f])
        if renametim:
            subprocess.run(['ncrename', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                            '-d', 'Time,time', f])
        if deletetim:
            with tempfile.NamedTemporaryFile(suffix='.nc') as tmp:
                subprocess.run(['ncks', '-Oh', '--fl_fmt=netcdf4_classic', '-L', '6',
                                '-x', '-v', 'Times', f, tmp.name])
            shutil.copyfile(tmp.name, f)
        dt = datetime.datetime.strptime(os.path.basename(f).split('.')[0], '%Y%m%d%H')
        with nc.Dataset(f, 'r+') as ncf:
            mv = ncf.missing_value
            for var in ncf.variables:
                if var.lower() in FIXEDVARS:
                    continue
                if np.issubdtype(ncf.variables[var].dtype, np.float):
                    v = ncf.variables[var][:]
                    v[np.logical_or(v==mv, v<=MVMIN)] = np.nan
                    ncf.variables[var][:] = v
            if 'time' not in ncf.variables:
                ncf.createVariable('time', 'f8', ('time',), zlib=True, complevel=6)
            ncf.variables['time'].units = 'hours since 1900-01-01'.encode('ascii')
            ncf.variables['time'].calendar = 'standard'.encode('ascii')
            ncf.variables['time'][0] = (dt - datetime.datetime(1900,1,1,0,0,0)).total_seconds() / 3600
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    main(args.files)
