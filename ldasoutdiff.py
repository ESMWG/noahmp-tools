#!/usr/bin/env python3
# -* - coding: utf-8 -*-


import os.path
import glob
import datetime
import numpy as np
import netCDF4 as nc
import argparse
import dateutil.parser

def main(caseroot, endtime):
    # find all outputs
    files = sorted(glob.glob(os.path.join(caseroot,'*.LDASOUT_DOMAIN1')), reverse=True)
    for iflnm, flnm in enumerate(files[:-1]):
        tc = datetime.datetime.strptime(os.path.basename(flnm).split('.')[0], '%Y%m%d%H')
        if (endtime is not None) and (tc > endtime):
            continue
        tp = datetime.datetime.strptime(os.path.basename(files[iflnm+1]).split('.')[0], '%Y%m%d%H')
        dt = tc - tp
        print(flnm)
        if dt.total_seconds() != 3 * 3600:
            print('missing file for ', tc - datetime.timedelta(hours=3))
            exit(1)
        with nc.Dataset(files[iflnm+1], 'r', keepweakref=True) as f:
            rnugdp = f.variables['UGDRNOFF'][:]
            rnsfcp = f.variables['SFCRNOFF'][:]
            snowp = f.variables['ACSNOW'][:]
            snomp = f.variables['ACSNOM'][:]
        with nc.Dataset(flnm, 'a', keepweakref=True) as f:
            rnugdc = f.variables['UGDRNOFF'][:]
            f.variables['UGDRNOFF'][:] = (rnugdc - rnugdp) / dt.total_seconds()
            f.variables['UGDRNOFF'].units = 'mm s-1'.encode('ascii')
            f.variables['UGDRNOFF'].description = 'underground runoff'.encode('ascii')

            rnsfcc = f.variables['SFCRNOFF'][:]
            f.variables['SFCRNOFF'][:] = (rnsfcc - rnsfcp) / dt.total_seconds()
            f.variables['SFCRNOFF'].units = 'mm s-1'.encode('ascii')
            f.variables['SFCRNOFF'].description = 'surface runoff'.encode('ascii')

            snowc = f.variables['ACSNOW'][:]
            f.variables['ACSNOW'][:] = (snowc - snowp) / dt.total_seconds()
            f.variables['ACSNOW'].units = 'mm s-1'.encode('ascii')
            f.variables['ACSNOW'].description = 'snow fall'.encode('ascii')

            snomc = f.variables['ACSNOM'][:]
            f.variables['ACSNOM'][:] = (snomc - snomp) / dt.total_seconds()
            f.variables['ACSNOM'].units = 'mm s-1'.encode('ascii')
            f.variables['ACSNOM'].description = 'melting water out of snow bottom'.encode('ascii')
    print(files[-1])
    with nc.Dataset(files[-1], 'a') as f:
        f.variables['UGDRNOFF'][:] = 0.0
        f.variables['UGDRNOFF'].units = 'mm s-1'.encode('ascii')
        f.variables['UGDRNOFF'].description = 'underground runoff'.encode('ascii')
        f.variables['SFCRNOFF'][:] = 0.0
        f.variables['SFCRNOFF'].units = 'mm s-1'.encode('ascii')
        f.variables['SFCRNOFF'].description = 'surface runoff'.encode('ascii')
        f.variables['ACSNOW'][:] = 0.0
        f.variables['ACSNOW'].units = 'mm s-1'.encode('ascii')
        f.variables['ACSNOW'].description = 'snow fall'.encode('ascii')
        f.variables['ACSNOM'][:] = 0.0
        f.variables['ACSNOM'].units = 'mm s-1'.encode('ascii')
        f.variables['ACSNOM'].description = 'melting water out of snow bottom'.encode('ascii')

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('caseroot')
    parser.add_argument('-e', '--endtime')
    args = parser.parse_args()
    if args.endtime is None:
        endtime = None
    else:
        endtime = dateutil.parser.parse(args.endtime)
    main(args.caseroot, endtime)
