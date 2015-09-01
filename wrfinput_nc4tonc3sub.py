#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import netCDF4 as nc


def copy_dim_def(ncout, ncin, dim_name):
    if dim_name not in ncin.dimensions:
        print('unknown dimension name: ' + dim_name)
        return
    if ncin.dimensions[dim_name].isunlimited():
        ncout.createDimension(dim_name, None)
    else:
        ncout.createDimension(dim_name, len(ncin.dimensions[dim_name]))
    return

def copy_var_def(ncout, ncin, var_name):
    if var_name not in ncin.variables:
        print('unknown variable name: ' + var_name)
        return
    dims = ncin.variables[var_name].dimensions
    dtyp = ncin.variables[var_name].dtype
    if hasattr(ncin.variables[var_name], '_FillValue'):
        fill_value = getattr(ncin.variables[var_name], '_FillValue')
    elif hasattr(ncin.variables[var_name], 'missing_value'):
        fill_value = getattr(ncin.variables[var_name], 'missing_value')
    else:
        fill_value = None
    ncout.createVariable(var_name, dtyp, dims, zlib=True, fill_value=fill_value)
    copy_attr(ncout, ncin, var_name)
    return

def copy_attr(ncout, ncin, var_name):
    if var_name not in ncin.variables or var_name not in ncout.variables:
        print('unknown variables name: ' + var_name)
        return
    for attr_name in ncin.variables[var_name].ncattrs():
        if attr_name in set(['_FillValue',]):
            continue
        setattr(ncout.variables[var_name],
                attr_name, getattr(ncin.variables[var_name], attr_name))
    return

def copy_var_val(ncout, ncin, var_name):
    if var_name not in ncin.variables or var_name not in ncout.variables:
        print('unknown variable name: ' + var_name)
        return
    old_mask = ncin.variables[var_name].mask
    old_scale = ncin.variables[var_name].scale
    ncin.variables[var_name].set_auto_mask(False)
    ncin.variables[var_name].set_auto_scale(False)
    ncout.variables[var_name][:] = ncin.variables[var_name][:]
    ncin.variables[var_name].set_auto_mask(old_mask)
    ncin.variables[var_name].set_auto_scale(old_scale)
    return

def main(fin, fout):
    with nc.Dataset(fin, 'r') as fi, \
         nc.Dataset(fout, 'w', format='NETCDF4_CLASSIC') as fo:
        for dim in ('Time', 'south_north', 'west_east'):
            copy_dim_def(fo, fi, dim)
        for var in ('HGT', 'ISLTYP', 'IVGTYP', 'TMN', 'XLAT', 'XLONG',
                    'XLAND', 'MAPFAC_MX', 'MAPFAC_MY'):
            copy_var_def(fo, fi, var)
        for var in ('HGT', 'ISLTYP', 'IVGTYP', 'TMN', 'XLAT', 'XLONG',
                    'XLAND', 'MAPFAC_MX', 'MAPFAC_MY'):
            copy_var_val(fo, fi, var)
        for att in ('DX', 'DY', 'GRID_ID',
                    'TRUELAT1', 'TRUELAT2', 'STAND_LON', 'MAP_PROJ',
                    'MMINLU',
                    'ISWATER', 'ISURBAN', 'ISICE', 'ISOILWATER'):
            setattr(fo, att, getattr(fi, att))
    return

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert WRFINPUT from NetCDF-4 format to NetCDF-3 format (subset, LDAS static fields only)')
    parser.add_argument('nc4file', type=str,
                        help='NetCDF-4 format WRFINPUT')
    parser.add_argument('nc3file', type=str,
                        help='NetCDF-3 format WRFINPUT')
    args = parser.parse_args()
    main(args.nc4file, args.nc3file)
