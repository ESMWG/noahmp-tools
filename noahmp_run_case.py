#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# run Noah-MP case
# author: Hui ZHENG

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

def run_resume_skip(dirname):
    '''run, resume, or skip'''
    resume = False
    exefile = os.path.join(dirname, NOAHMP_EXE)
    namelist = os.path.join(dirname, NAMELIST)
    nml = f90nml.read(namelist)
    dt_end = datetime.datetime(nml['noahlsm_offline']['start_year'],
                               nml['noahlsm_offline']['start_month'],
                               nml['noahlsm_offline']['start_day'],
                               nml['noahlsm_offline']['start_hour'],
                               nml['noahlsm_offline']['start_min']) \
        + datetime.timedelta(days=nml['noahlsm_offline']['kday'])
    curdir = os.getcwd()
    os.chdir(dirname)
    # 1. determing skip, resume, or run
    resfiles = sorted(glob.glob(os.path.join(dirname, 'RESTART.*_DOMAIN[0-9]')))
    resfile_nml = nml['noahlsm_offline'].get('restart_filename_requested')
    resfile_nml = os.path.abspath(resfile_nml) if resfile_nml is not None else resfile_nml
    if len(resfiles) == 0:
        # run
        resume = False
    else:
        # skip, run, resume
        if dt_end == datetime.datetime.strptime(os.path.basename(resfiles[-1])[8:18], '%Y%m%d%H'):
            # skip
            return False
        elif (len(resfiles) == 1) and resfile_nml == os.path.abspath(resfiles[0]):
            # run
            resume = False
        else:
            # resume
            resume = True
    # resume or run
    if not resume:
        # 1. fresh case
        subprocess.check_call([exefile,], stdout=sys.stdout, stderr=sys.stderr,
                              universal_newlines=True)
    else:
        # 2. resume and run
        # prepare namelist
        namelist_bak = namelist + '-orig-before-resume'
        os.rename(namelist, namelist_bak)
        resfile = os.path.abspath(resfiles[max(len(resfiles) - 1, 0)])
        dt_res = datetime.datetime.strptime(os.path.basename(resfile)[8:18], '%Y%m%d%H')
        kday = (dt_end - dt_res).days
        nml['noahlsm_offline']['start_year'] = dt_res.year
        nml['noahlsm_offline']['start_month'] = dt_res.month
        nml['noahlsm_offline']['start_day'] = dt_res.day
        nml['noahlsm_offline']['start_hour'] = dt_res.hour
        nml['noahlsm_offline']['start_min'] = dt_res.minute
        nml['noahlsm_offline']['restart_filename_requested'] = resfile
        nml['noahlsm_offline']['kday'] = kday
        nml.write(namelist)
        # run
        subprocess.check_call([exefile,], stdout=sys.stdout, stderr=sys.stderr,
                              universal_newlines=True)
        # finish
        os.remove(namelist)
        os.rename(namelist_bak, namelist)
    os.chdir(curdir)
    return True                 # run or resume

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

def main(caseroot, fresh=True):
    caseroot = os.path.abspath(caseroot)
    predir = None
    curdir = None
    # find out spinups
    print(caseroot)
    spinupdirs = glob.glob(os.path.join(caseroot,'spinup-*'))

    hasresume = False
    # run spinups
    for dirname in sorted(spinupdirs):
        print('RUN_CASE: ' + dirname)
        predir, curdir = curdir, dirname
        process_restart(predir, curdir)
        if fresh or hasresume:
            run(curdir)
        else:
            hasresume = run_resume_skip(curdir)
    
    # run case
    print('RUN_CASE: ' + caseroot)
    predir, curdir = curdir, caseroot
    process_restart(predir, curdir)
    if fresh or hasresume:
        run(curdir)
    else:
        run_resume_skip(curdir)
    pass

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run Noah-MP case')
    parser.add_argument('caseroot', type=str,
                        help='top-level directory of Noah-MP case')
    parser.add_argument('-f', '--fresh', default=False,
                        action="store_true", help='treat as a fresh case')
    args = parser.parse_args()
    if not os.path.isdir(args.caseroot):
        print('Error: directory (' + args.caseroot + ') is not a valid caseroot!')
        sys.exit(1)
    main(args.caseroot, fresh=args.fresh)
