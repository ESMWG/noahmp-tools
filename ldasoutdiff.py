#!/usr/bin/env python3
# -* - coding: utf-8 -*-


import os.path
import glob
import datetime
import numpy as np
import netCDF4 as nc
import argparse

def main(caseroot):
    # find all outputs
    files = sorted(glob.glob(os.path.join(caseroot,'*.LDASOUT_DOMAIN1')), reverse=True)
    for iflnm, flnm in enumerate(files[:-1]):
        tc = datetime.datetime.strptime(os.path.basename(flnm).split('.')[0], '%Y%m%d%H')
        tp = datetime.datetime.strptime(os.path.basename(files[iflnm+1]).split('.')[0], '%Y%m%d%H')
        dt = tc - tp
        print(flnm)
        if dt.total_seconds() != 3 * 3600:
            print('missing file for ', tc - datetime.timedelta(hours=3))
            exit(1)
        with nc.Dataset(flnm, 'r+') as fc, \
             nc.Dataset(files[iflnm+1], 'r') as fp:
            rnugdp = fp.variables['UGDRNOFF'][:]
            rnugdc = fc.variables['UGDRNOFF'][:]
            fc.variables['UGDRNOFF'][:] = (rnugdc - rnugdp) / dt.total_seconds()
            fc.variables['UGDRNOFF'].units = 'mm s-1'.encode('ascii')
            fc.variables['UGDRNOFF'].description = 'underground runoff'.encode('ascii')

            rnsfcp = fp.variables['SFCRNOFF'][:]
            rnsfcc = fc.variables['SFCRNOFF'][:]
            fc.variables['SFCRNOFF'][:] = (rnsfcc - rnsfcp) / dt.total_seconds()
            fc.variables['SFCRNOFF'].units = 'mm s-1'.encode('ascii')
            fc.variables['SFCRNOFF'].description = 'surface runoff'.encode('ascii')

            snowp = fp.variables['ACSNOW'][:]
            snowc = fc.variables['ACSNOW'][:]
            fc.variables['ACSNOW'][:] = (snowc - snowp) / dt.total_seconds()
            fc.variables['ACSNOW'].units = 'mm s-1'.encode('ascii')
            fc.variables['ACSNOW'].description = 'snow fall'.encode('ascii')

            snomp = fp.variables['ACSNOM'][:]
            snomc = fc.variables['ACSNOM'][:]
            fc.variables['ACSNOM'][:] = (snomc - snomp) / dt.total_seconds()
            fc.variables['ACSNOM'].units = 'mm s-1'.encode('ascii')
            fc.variables['ACSNOM'].description = 'melting water out of snow bottom'.encode('ascii')
    print(files[-1])
    with nc.Dataset(files[-1], 'r+') as fc:
        fc.variables['UGDRNOFF'][:] = 0.0
        fc.variables['UGDRNOFF'].units = 'mm s-1'.encode('ascii')
        fc.variables['UGDRNOFF'].description = 'underground runoff'.encode('ascii')
        fc.variables['SFCRNOFF'][:] = 0.0
        fc.variables['SFCRNOFF'].units = 'mm s-1'.encode('ascii')
        fc.variables['SFCRNOFF'].description = 'surface runoff'.encode('ascii')
        fc.variables['ACSNOW'][:] = 0.0
        fc.variables['ACSNOW'].units = 'mm s-1'.encode('ascii')
        fc.variables['ACSNOW'].description = 'snow fall'.encode('ascii')
        fc.variables['ACSNOM'][:] = 0.0
        fc.variables['ACSNOM'].units = 'mm s-1'.encode('ascii')
        fc.variables['ACSNOM'].description = 'melting water out of snow bottom'.encode('ascii')

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('caseroot')
    args = parser.parse_args()
    main(args.caseroot)
