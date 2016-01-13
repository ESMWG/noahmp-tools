#!/usr/bin/env python3
# -* - coding: utf-8 -*-


import datetime
import numpy as np
import netCDF4 as nc
import argparse

def main(casefile):
    # find all outputs
    with nc.Dataset(casefile, 'r+') as f:
        ntim = len(f.dimensions['time'])
        tim = nc.num2date(f.variables['time'][:], f.variables['time'].units)
        dt = tim[-1] - tim[-2]
        for itim in reversed(range(1,ntim)):
            rnugdp = f.variables['UGDRNOFF'][itim-1,...]
            rnugdc = f.variables['UGDRNOFF'][itim,...]
            rnugdd = (rnugdc - rnugdp) / dt.total_seconds()
            f.variables['UGDRNOFF'][itim,...] = rnugdd

            rnsfcp = f.variables['SFCRNOFF'][itim-1,...]
            rnsfcc = f.variables['SFCRNOFF'][itim,...]
            rnsfcd = (rnsfcc - rnsfcp) / dt.total_seconds()
            f.variables['SFCRNOFF'][itim,...] = rnsfcd

            snowp = f.variables['ACSNOW'][itim-1,...]
            snowc = f.variables['ACSNOW'][itim,...]
            snowd = (snowc - snowp) / dt.total_seconds()
            f.variables['ACSNOW'][itim,...] = snowd

            snomp = f.variables['ACSNOM'][itim-1,...]
            snomc = f.variables['ACSNOM'][itim,...]
            snomd = (snomc - snomp) / dt.total_seconds()
            f.variables['ACSNOM'][itim,...] = snomd

        f.variables['UGDRNOFF'][0,...] = 0.0
        f.variables['SFCRNOFF'][0,...] = 0.0
        f.variables['ACSNOW'][0,...] = 0.0
        f.variables['ACSNOM'][0,...] = 0.0

        f.variables['UGDRNOFF'].units = 'mm s-1'.encode('ascii')
        f.variables['UGDRNOFF'].description = 'underground runoff'.encode('ascii')
        f.variables['SFCRNOFF'].units = 'mm s-1'.encode('ascii')
        f.variables['SFCRNOFF'].description = 'surface runoff'.encode('ascii')
        f.variables['ACSNOW'].units = 'mm s-1'.encode('ascii')
        f.variables['ACSNOW'].description = 'snow fall'.encode('ascii')
        f.variables['ACSNOM'].units = 'mm s-1'.encode('ascii')
        f.variables['ACSNOM'].description = 'melting water out of snow bottom'.encode('ascii')

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    args = parser.parse_args()
    main(args.output)
