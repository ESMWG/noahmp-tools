#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# delete useless variables, permute dimensions

import os
import glob
import subprocess
import argparse
import tempfile


def strip_output(directory):
    files = glob.glob(os.path.join(directory, '*.LDASOUT_DOMAIN[0-9]'))
    for f in files:
        print(f)
        with tempfile.NamedTemporaryFile() as tmp:
            subprocess.call(['ncks', '-O', '--fl_fmt=netcdf4_classic', '-h', '-x', '-v', 'BBXY,SATPSIXY,SATDKXY,MAXSMCXY,REFSMCXY,WLTSMCXY', f, tmp.name])
            subprocess.call(['ncpdq', '-O', '--fl_fmt=netcdf4_classic', '-h', '-a', 'Time,snow_layers,soil_layers_stag,south_north,west_east', tmp.name, f])
    return

def main(dirs):
    for d in dirs:
        strip_output(d)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='strip useless variables, permute dimensions')
    parser.add_argument('dir', nargs='+', type=str)
    args = parser.parse_args()
    main(args.dir)
