#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# read initial state from Noah-MP output and write them to wrfinput
# author: Hui ZHENG

from __future__ import absolute_import, unicode_literals, division

import numpy as np
import netCDF4 as nc

nmp2wrf_3d = {'SOIL_T':'TSLB',
              'SNOW_T':'TSNO',
              'SMC':'SMOIS',
              'SH2O':'SH2O',
              'ZSNSO':'ZSNSO',
              'SNICE':'SNICE',
              'SNLIQ':'SNLIQ'}

nmp2wrf_2d = {'QSNOW':'QSNOWXY',
              'FWET':'FWET',
              'SNEQVO':'SNEQVO',
              'EAH':'EAH',
              'TAH':'TAH',
              'ALBOLD':'ALBOLD',
              'CM':'CM',
              'CH':'CH',
              'ISNOW':'ISNOW',
              'CANLIQ':'CANLIQ',
              'CANICE':'CANICE',
              'SNOWH':'SNOWH',
              'TV':'TV',
              'TG':'TG',
              'ZWT':'ZWT',
              'WA':'WA',
              'WT':'WT',
              'WSLAKE':'WSLAKE',
              'LFMASS':'LFMASS',
              'RTMASS':'RTMASS',
              'STMASS':'STMASS',
              'WOOD':'WOOD',
              'STBLCP':'STBLCP',
              'FASTCP':'FASTCP',
              'FDEPTHXY':'FDEPTH',
              'RIVERBEDXY':'RIVERBED',
              'EQZWT':'EQZWT',
              'RIVERCONDXY':'RIVERCOND',
              'PEXPXY':'PEXP'}
ABSMAX = 1.0e20

def main(nmpfile, wrffile):
    with nc.Dataset(nmpfile, 'r') as fi, \
         nc.Dataset(wrffile, 'r+') as fo:
        for varnamei, varnameo in nmp2wrf_2d.items():
            print(varnamei, varnameo)
            vi = fi.variables[varnamei][:]
            vo = fo.variables[varnameo][:]
            mask = np.abs(vi) >= ABSMAX
            v = np.where(mask, vo, vi)
            fo.variables[varnameo][:] = v[:]
        for varnamei, varnameo in nmp2wrf_3d.items():
            print(varnamei, varnameo)
            vi = fi.variables[varnamei][:]
            vi = np.swapaxes(vi, 1, 2)
            vo = fo.variables[varnameo][:]
            mask = np.abs(vi) >= ABSMAX
            v = np.where(mask, vo, vi)
            fo.variables[varnameo][:] = v[:]
        fo.variables['FNDSNOWH'][:] = 1
    return

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy land state from Noah-MP output to WRF.')
    parser.add_argument('nmpfile', type=str,
                        help='Noah-MP Restart file')
    parser.add_argument('wrffile', type=str,
                        help='WRF input file')
    args = parser.parse_args()
    main(args.nmpfile, args.wrffile)
