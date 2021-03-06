#!/usr/bin/env python

# Copyright (c) 2014, the GREAT3 executive committee (http://www.great3challenge.info/?q=contacts)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other materials provided with
# the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to
# endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

description="""
Get all the md5sums for all the branches in the experiments, obs_types, shear_types lists in
validation/constants.py.

Writes a full md5sum output file with each entry in the format <MD5 checksum> <filename> to the
specified outfile.
"""
 
import os
import constants

def get_md5sum(filename, md5sum_exec="md5sum", silent=True):
    """Run md5sum on the given filename.

    @return A string containing "<MD5 checksum> experiment/obs_type/shear_type/"
    """
    import subprocess
    import tempfile
    tmpfile = tempfile.mktemp()
    with open(tmpfile, "wb") as ftmp:
        retcode = subprocess.check_call(
            [md5sum_exec, filename], stdout=ftmp)
    with open(tmpfile, "rb") as ftmp:
        retstring = ftmp.readline()
    os.remove(tmpfile) # Tidy up
    if not silent:
        print retstring
    return retstring

def collate_all(root_dir, outfile, experiments=constants.experiments, obs_types=constants.obs_types,
                shear_types=constants.shear_types, md5sum_exec="md5sum"):
    """Put together a file containing an <MD5 checksum> <filename> entry for every file in the
    all the experiment/obs_type/shear_type folders specified.
    """
    import sys
    import glob
    sys.path.append("..")
    import great3sims.mapper
    # Save the folders in which files were found
    found_exps = []
    found_obs = []
    found_shears = []
    with open(outfile, "wb") as fout:
        for experiment in experiments:

            for obs_type in obs_types:

                for shear_type in shear_types:

                    # Get *all* the files in this folder
                    mapper = great3sims.mapper.Mapper(root_dir, experiment, obs_type, shear_type) 
                    allfiles = glob.glob(os.path.join(mapper.full_dir, "*"))
                    if len(allfiles) > 0:
                        if experiment not in found_exps: found_exps.append(experiment)
                        if obs_type not in found_obs: found_obs.append(obs_type)
                        if shear_type not in found_shears: found_shears.append(shear_type)
                        print "Getting md5sum for all files in "+str(mapper.full_dir)
                        for checkfile in allfiles:

                            fout.write(get_md5sum(checkfile, silent=True))

    print "Ran md5sum on all files in "+root_dir
    print "Found files for experiments "+str(found_exps)
    print "Found files for obs_types "+str(found_obs)
    print "Found files for shear_types "+str(found_shears)
    print "Full md5sum list written to "+str(outfile)
    return


if __name__ == "__main__":

    import optparse

    parser = optparse.OptionParser(description=description)
    parser.add_option(
        '--root_dir', default=str(constants.public_dir),
        help="Root directory for the GREAT3 release for which you want to calculate md5sums "+
        "[default = "+str(constants.public_dir)+"]")
    parser.add_option(
        "--md5sum", default="md5sum",
        help="Path to md5sum executable [default = md5sum]") 
    args, outfile = parser.parse_args()
    if len(outfile) == 0 or len(outfile) > 1:
        print outfile
        print "Please supply one outfile, and place it *before* optional inputs!"
        print "usage: get_md5sums.py outfile [--root_dir=ROOT_DIR] [--md5sum=MD5SUM] [-h]"
        exit(1)
    collate_all(args.root_dir, outfile[0], md5sum_exec=args.md5sum)

