#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# run Noah-MP case
# author: Hui ZHENG
# date: 2015-03-22

import sys
import os
import os.path
import glob
import subprocess
import shutil
import datetime
import netCDF4 as nc
import f90nml

NOAHMP_EXE = 'noahmp_hrldas.exe'
NAMELIST = 'namelist.hrldas'

def run(dirname):
    exefile = os.path.join(dirname, NOAHMP_EXE)
    curdir = os.getcwd()
    os.chdir(dirname)
    subprocess.check_call([exefile,], stdout=sys.stdout, stderr=sys.stderr,
                          universal_newlines=True)
    os.chdir(curdir)
    return

def process_restart(predir, curdir):
    if predir is None:
        return
    prenml = f90nml.read(os.path.join(predir, NAMELIST))
    curnml = f90nml.read(os.path.join(curdir, NAMELIST))
    prebeg = datetime.datetime(prenml['noahlsm_offline']['start_year'],
                               prenml['noahlsm_offline']['start_month'],
                               prenml['noahlsm_offline']['start_day'],
                               prenml['noahlsm_offline']['start_hour'],
                               prenml['noahlsm_offline']['start_min'])
    preend = prebeg + datetime.timedelta(days=prenml['noahlsm_offline']['kday'])
    preres = os.path.join(predir,
                          'RESTART.' + preend.strftime('%Y%m%d%H') + '_DOMAIN1')
    curbeg = datetime.datetime(curnml['noahlsm_offline']['start_year'],
                               curnml['noahlsm_offline']['start_month'],
                               curnml['noahlsm_offline']['start_day'],
                               curnml['noahlsm_offline']['start_hour'],
                               curnml['noahlsm_offline']['start_min'])
    curres = os.path.join(curdir,
                          curnml['noahlsm_offline']['restart_filename_requested'])
    shutil.copy(preres, curres)
    with nc.Dataset(curres, 'r+') as f:
        f.variables['Times'][0,:] = nc.stringtoarr(curbeg.strftime('%Y-%m-%d_%H:%M:%S'), 19)
    return

def main(caseroot):
    caseroot = os.path.abspath(caseroot)
    predir = None
    curdir = None
    # find out spinups
    print(caseroot)
    spinupdirs = glob.glob(os.path.join(caseroot,'spinup-*'))

    # run spinups
    for dirname in sorted(spinupdirs):
        print('RUN_CASE: ' + dirname)
        predir, curdir = curdir, dirname
        process_restart(predir, curdir)
        run(dirname)
    
    # run case
    print('RUN_CASE: ' + caseroot)
    predir, curdir = curdir, caseroot
    process_restart(predir, curdir)
    run(caseroot)
    pass

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run Noah-MP case')
    parser.add_argument('caseroot', type=str,
                        help='top-level directory of Noah-MP case')
    args = parser.parse_args()
    if not os.path.isdir(args.caseroot):
        print('Error: directory (' + args.caseroot + ') is not a valid caseroot!')
        sys.exit(1)
    main(args.caseroot)
