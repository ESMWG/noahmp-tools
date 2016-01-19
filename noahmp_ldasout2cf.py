#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# convert NoahMP outputs to CF-compatible files


import sys
import os
import glob
import datetime
import argparse
import dateutil.parser
import numpy as np
import netCDF4 as nc
np.seterr(invalid='ignore')


TDIM = 'time'
TVAR = 'TIMES'
timeunits = 'hours since 1900-01-01'
XDIM = 'west_east'
XVAR = 'WEST_EAST'
YDIM = 'south_north'
YVAR = 'SOUTH_NORTH'
ACCVARS = ['ACSNOW', 'ACSNOM', 'SFCRNOFF', 'UGDRNOFF']
VALIDMIN = -1e10

def datetime4name(filename):
    timestr = os.path.basename(filename).split('.')[0]
    return datetime.datetime.strptime(timestr, '%Y%m%d%H')

def source_info(datadir, begtime, endtime):
    allfiles = sorted(glob.glob(os.path.join(datadir, '*.LDASOUT_DOMAIN1')))
    files = [x for x in allfiles
             if datetime4name(x) >= begtime and datetime4name(x) < endtime]
    timestep = 0
    integrity = False
    if len(files) > 1:
        timesteps = set()
        for ifile in range(1,len(files)):
            timesteps.add((datetime4name(files[ifile]) - datetime4name(files[ifile-1])).total_seconds())
        timestep = timesteps.pop()
        if len(timesteps) == 0 \
           and ((datetime4name(files[0]) - begtime).total_seconds() < timestep) \
           and ((endtime - datetime4name(files[-1])).total_seconds() <= timestep):
            integrity = True
    return files, timestep, integrity

def define_output(wrfinput, fi, fo):
    # inquire spatial dimension from wrfinput
    with nc.Dataset(wrfinput, 'r') as fwrf:
        if fwrf.MAP_PROJ == 6:
            lat2d = np.squeeze(fwrf.variables['XLAT'][:])
            lon2d = np.squeeze(fwrf.variables['XLONG'][:])
            lat = lat2d[:,0]
            lon = lon2d[0,:]
        else:
            lat = None
            lon = None
    # create Dimension
    dimset = set()
    for var in fi.variables:
        if var.upper() in [TVAR, XVAR, YVAR]:
            continue
        dimset.update((x.lower() for x in fi.variables[var].dimensions))
    for dim in dimset:
        if dim == TDIM:
            fo.createDimension(dim, None)
        else:
            fo.createDimension(dim, len(fi.dimensions[dim]))
    # create vars
    fo.createVariable(XDIM, 'f', (XDIM,), zlib=True, complevel=6)
    fo.variables[XDIM].standard_name = 'longitude'.encode('ascii')
    fo.variables[XDIM].units = 'degree_east'.encode('ascii')
    fo.variables[XDIM].axis = 'X'.encode('ascii')
    fo.variables[XDIM][:] = lon
    fo.createVariable(YDIM, 'f', (YDIM,), zlib=True, complevel=6)
    fo.variables[YDIM].standard_name = 'latitude'.encode('ascii')
    fo.variables[YDIM].units = 'degree_north'.encode('ascii')
    fo.variables[YDIM].axis = 'Y'.encode('ascii')
    fo.variables[YDIM][:] = lat
    for var in fi.variables:
        if var.upper() == TVAR:
            fo.createVariable(TDIM, 'f8', (TDIM,), zlib=True, complevel=6)
            fo.variables[TDIM].standard_name = 'time'.encode('ascii')
            fo.variables[TDIM].units = timeunits.encode('ascii')
            fo.variables[TDIM].calendar = 'standard'.encode('ascii')
            fo.variables[TDIM].axis = 'T'.encode('ascii')
        elif var.upper() in set([XVAR, YVAR]):
            pass
        elif var.upper() not in ACCVARS:
            dtype = fi.variables[var].dtype
            dims = [x.lower() for x in fi.variables[var].dimensions]
            dims_n = []
            if TDIM in dims:
                dims.remove(TDIM)
                dims_n.append(TDIM)
            if YDIM in dims:
                dims.remove(YDIM)
                dims_n.append(YDIM)
            if XDIM in dims:
                dims.remove(XDIM)
                dims_n.append(XDIM)
            if len(dims) > 1:
                print("don't support multiple z-axis: " + str(dims) + ' of ' + var)
                sys.exit(1)
            elif len(dims) == 1:
                zdim = dims[0]
                dims_n.insert(1, zdim)
            if np.issubdtype(dtype, np.float):
                fo.createVariable(var, dtype, dims_n,
                                  zlib=True, complevel=6, fill_value=np.nan)
            else:
                fo.createVariable(var, dtype, dims_n, zlib=True, complevel=6)
            for att in fi.variables[var].ncattrs():
                attval = fi.variables[var].getncattr(att)
                if isinstance(fi.variables[var].getncattr(att), str):
                    attval = attval.encode('ascii')
                fo.variables[var].setncattr(att, attval)
        else:                   # ACCVARS
            dtype = fi.variables[var].dtype
            dims = [x.lower() for x in fi.variables[var].dimensions]
            if np.issubdtype(dtype, np.float):
                fo.createVariable(var, dtype, dims_n,
                                  zlib=True, complevel=6, fill_value=np.nan)
            else:
                fo.createVariable(var, dtype, dims_n, zlib=True, complevel=6)
            for att in fi.variables[var].ncattrs():
                attval = fi.variables[var].getncattr(att)
                if att.lower() == 'units':
                    attval = (attval + ' s-1').encode('ascii')
                elif att.lower() == 'description':
                    attval = attval.lower().replace('accumulated ', '').replace('accumulatetd ','').encode('ascii')
                elif isinstance(fi.variables[var].getncattr(att), str):
                    attval = attval.encode('ascii')
                fo.variables[var].setncattr(att, attval)
    for att in fi.ncattrs():
        if isinstance(fi.getncattr(att), str):
            fo.setncattr(att, fi.getncattr(att).encode('ascii'))
        else:
            fo.setncattr(att, fi.getncattr(att))
    return

def copy_var(fi, fo, var, ind):
    if var.lower() in [TDIM, XDIM, YDIM] \
       or var.upper() in [TVAR, XVAR, YVAR] \
       or var.upper() in ACCVARS:
        return
    # mask invalid value
    fi.variables[var].set_auto_maskandscale(False)
    fo.variables[var].set_auto_maskandscale(False)
    v = fi.variables[var][:]

    if np.issubdtype(fi.variables[var].dtype, np.float):
        v[v <= VALIDMIN] = np.nan

    # swap dimension
    dims = [x.lower() for x in fi.variables[var].dimensions]
    zdim = set(dims) - set([TDIM, XDIM, YDIM])
    if len(zdim) == 1:
        zdim = zdim.pop()
        v = np.swapaxes(v, dims.index(zdim), 1)
    fo.variables[var][ind,...] = v
    return

def acc2flx(fic, fip, fo, var, ind, ts):
    if var.upper() not in ACCVARS:
        return
    fic.variables[var].set_auto_maskandscale(False)
    fip.variables[var].set_auto_maskandscale(False)
    fo.variables[var].set_auto_maskandscale(False)
    vc = fic.variables[var][:]
    vp = fip.variables[var][:]
    vc[vc <= VALIDMIN] = np.nan
    vp[vp <= VALIDMIN] = np.nan
    fo.variables[var][ind,...] = (vc - vp) / ts
    return

def main(wrfinput, datadir, outfile, begtime, endtime, partially=False):
    files, timestep, integrity = source_info(datadir, begtime, endtime)
    if (not integrity) and (not partially):
        print('not enough files (try --partially)')
        sys.exit(1)
    with nc.Dataset(outfile, 'w') as fo:
        for ifile in range(len(files)):
            print(files[ifile])
            with nc.Dataset(files[ifile], 'r') as fi:
                if ifile == 0:
                    define_output(wrfinput, fi, fo)
                fo.variables[TDIM][ifile] = nc.date2num(datetime4name(files[ifile]),
                                                        fo.variables[TDIM].units)
                for var in fi.variables:
                    if var.upper() in ACCVARS:
                        continue
                    copy_var(fi, fo, var, ifile)
        print('acc to flux')
        for ifile in reversed(range(1,len(files))):
            with nc.Dataset(files[ifile], 'r') as fic, \
                 nc.Dataset(files[ifile-1], 'r') as fip:
                for var in ACCVARS:
                    acc2flx(fic, fip, fo, var, ifile, timestep)
        startfile = os.path.join(datadir,
                                 (datetime4name(files[0]) - datetime.timedelta(seconds=timestep)).strftime('%Y%m%d%H') + '.LDASOUT_DOMAIN1')
        if os.path.exists(startfile):
            with nc.Dataset(files[0], 'r') as fic, \
                 nc.Dataset(startfile, 'r') as fip:
                for var in ACCVARS:
                    acc2flx(fic, fip, fo, var, 0, timestep)
        else:
            for var in ACCVARS:
                fo.variables[var][0,...] = fo.variables[var][1,...]
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert NoahMP outputs to single CF-compatible file')
    parser.add_argument('wrfinput')
    parser.add_argument('datadir', help='root directory of raw NoahMP outputs')
    parser.add_argument('outfile', help='CF-compaible output file')
    parser.add_argument('begtime', help='inclusive')
    parser.add_argument('endtime', help='exclusive')
    parser.add_argument('--partially', action='store_true')
    args = parser.parse_args()
    main(args.wrfinput, args.datadir, args.outfile,
         dateutil.parser.parse(args.begtime),
         dateutil.parser.parse(args.endtime),
         args.partially)
