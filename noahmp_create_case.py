#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# create Noah-MP case

import sys
import os
import os.path
import datetime
import string
import shutil

namelist = """

"""
NOAHMP_TBLS = ['GENPARM.TBL', 'MPTABLE.TBL', 'SOILPARM.TBL', 'VEGPARM.TBL']
NOAHMP_EXE = 'noahmp_hrldas.exe'

def main(modelroot=None,
         caseroot='unknown_case',
         dtbeg_s=None, dtbeg=None, dtend=None, nloop=0,
         namelist_template=None, forcing=None, wrfinput=None,
         delete=False):
    if (modelroot is None) or (dtbeg is None) or (dtend is None):
        return
    caseroot = os.path.abspath(caseroot)
    if forcing is None:
        forcing = os.path.join(caseroot, 'ldasin')
    else:
        forcing = os.path.abspath(forcing)
    if wrfinput is None:
        wrfinput = os.path.join(caseroot, 'wrfinput_d01')
    else:
        wrfinput = os.path.abspath(wrfinput)
    os.makedirs(caseroot, exist_ok=True)
    os.makedirs(forcing, exist_ok=True)

    if namelist_template is None:
        namelist_template = os.path.join(modelroot, 'namelist.hrldas.template')
    if not os.path.isfile(namelist_template):
        print('file (' + namelist_template + ') does not exist!')
        return

    # load namelist
    with open(namelist_template, 'rt') as f:
        namelist = string.Template(f.read())

    # have spinup
    if (dtbeg_s is not None) and (dtbeg_s < dtbeg):
        havespinup = True
        if nloop is None or nloop < 1: nloop = 1
    else:
        havespinup = False
    
    # run
    for f in NOAHMP_TBLS + [NOAHMP_EXE, ]:
        shutil.copy(os.path.join(modelroot, f),
                    os.path.join(caseroot, f))
    if havespinup:
        resfile = 'RESTART.' + dtbeg.strftime('%Y%m%d%H') + '_DOMAIN1'
        nml = namelist.safe_substitute(START_YEAR=dtbeg.year,
                                       START_MONTH=dtbeg.month,
                                       START_DAY=dtbeg.day,
                                       START_HOUR=dtbeg.hour,
                                       START_MIN=dtbeg.minute,
                                       KDAY=(dtend-dtbeg).days,
                                       INDIR=forcing,
                                       OUTDIR=caseroot,
                                       WRFINPUT=wrfinput,
                                       RESON='',
                                       RESFILE=resfile)
    else:
        nml = namelist.safe_substitute(START_YEAR=dtbeg.year,
                                       START_MONTH=dtbeg.month,
                                       START_DAY=dtbeg.day,
                                       START_HOUR=dtbeg.hour,
                                       START_MIN=dtbeg.minute,
                                       KDAY=(dtend-dtbeg).days,
                                       INDIR=forcing,
                                       OUTDIR=caseroot,
                                       WRFINPUT=wrfinput,
                                       RESON='!')
    with open(os.path.join(caseroot, 'namelist.hrldas'), 'wt') as f:
        f.write(nml)

    # spinup
    havespinup = False
    if (nloop > 0) and (dtbeg_s is not None) and (dtbeg_s < dtbeg):
        havespinup = True
        for iloop in range(nloop):
            fold = os.path.join(caseroot, 'spinup-{0:03d}'.format(iloop+1))
            os.makedirs(fold, exist_ok=True)
            for f in NOAHMP_TBLS + [NOAHMP_EXE]:
                fabs = os.path.join(fold, f)
                if os.path.isfile(fabs) : os.remove(fabs)
                os.symlink(os.path.join(caseroot, f), fabs)
            if iloop == 0:
                nml = namelist.safe_substitute(START_YEAR=dtbeg_s.year,
                                               START_MONTH=dtbeg_s.month,
                                               START_DAY=dtbeg_s.day,
                                               START_HOUR=dtbeg_s.hour,
                                               START_MIN=dtbeg_s.minute,
                                               KDAY=(dtbeg-dtbeg_s).days,
                                               INDIR=forcing,
                                               OUTDIR=fold,
                                               WRFINPUT=wrfinput,
                                               RESON='!')
            else:
                resfile = 'RESTART.' + dtbeg_s.strftime('%Y%m%d%H') + '_DOMAIN1'
                nml = namelist.safe_substitute(START_YEAR=dtbeg_s.year,
                                               START_MONTH=dtbeg_s.month,
                                               START_DAY=dtbeg_s.day,
                                               START_HOUR=dtbeg_s.hour,
                                               START_MIN=dtbeg_s.minute,
                                               KDAY=(dtbeg-dtbeg_s).days,
                                               INDIR=forcing,
                                               OUTDIR=fold,
                                               WRFINPUT=wrfinput,
                                               RESON='',
                                               RESFILE=resfile)
            with open(os.path.join(fold, 'namelist.hrldas'), 'wt') as f:
                f.write(nml)
    pass

import argparse
import dateutil.parser
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download NARR 3-hourly product from NOMADS.')
    parser.add_argument('caseroot', type=str,
                        default=os.getcwd(), help='case root directory')
    parser.add_argument('-m', '--modelroot', type=str,
                        default=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                             'noahmp'),
                        help='Noah-MP root root directory')
    parser.add_argument('-n', '--namelist', type=str,
                        help='noahmp namelist template location. (default: MODELROOT/namelist.template)')
    parser.add_argument('-f', '--forcing', type=str,
                        help='top-level directory under which the forcing files are stored. (default: CASEROOT/ldasin)')
    parser.add_argument('-i', '--wrfinput', type=str,
                        help='location of wrfinput file. (default: CASEROOT/wrfinput_d01)')
    parser.add_argument('-b', '--begtime', required=True,
                        help='start date and time', type=str)
    parser.add_argument('-e', '--endtime', required=True,
                        help='end date and time (exclusive)', type=str)
    parser.add_argument('-bs', '--begtimespinup',
                        help='start date and time of spinup', type=str)
    parser.add_argument('-l', '--nloop',
                        help='number of spinup loops (default: 0 or 1 for no spinup)',
                        default=1, type=int)
    parser.add_argument('-d', '--delete',
                        help='delete old case', default=False, action='store_true')
    args = parser.parse_args()

    main(modelroot=args.modelroot,
         caseroot=args.caseroot,
         dtbeg_s=dateutil.parser.parse(args.begtimespinup) if args.begtimespinup is not None else None,
         dtbeg=dateutil.parser.parse(args.begtime),
         dtend=dateutil.parser.parse(args.endtime),
         nloop=args.nloop,
         namelist_template=args.namelist,
         forcing=args.forcing,
         wrfinput=args.wrfinput,
         delete=args.delete)
