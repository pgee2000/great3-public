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
"""@file count_objects.py

A command line executable script for running SExtractor on all FITS files in a given GREAT3
experiment (using a sensible default config, chosen after some trial and error) to determine object
counts for GREAT3 images.  The idea is there are supposed to be 10000 galaxy objects per image.

Saves output stored into dictionaries into a counts/ subdirectory for later checking.
"""

import os
import sys
import glob
import pyfits
import constants
sys.path.append("..")
import great3sims.mapper

def file_count(filename, sex_exec="/usr/local/bin/sex", silent=False, config_filename="sex.config"):
    """Run SExtractor on the given `filename`.

    @param sex_exec        Executable file for SExtractor (default=`/usr/local/bin/sex`)
    @param silent          Run silently (stdout & stderr pipe to temporary file, default=`True`)
    @param config_filename Filename for the SExtractor configuation file (default=`sex.config`)

    @return Number of objects detected in the file
    """
    import subprocess
    import tempfile
    # Make a unique (safe) tempfile to which to write the FITS-format catalog
    catfile_descriptor, catfile = tempfile.mkstemp(suffix=".fits")
    # Close the catfile unit (it's currently open after creation)
    os.close(catfile_descriptor)
    if silent:
        fdtmp, stdoutfile = tempfile.mkstemp()
        with os.fdopen(fdtmp, "wb") as fotmp:
            subprocess.check_call(
                [sex_exec, filename, "-c", config_filename, "-CATALOG_NAME", catfile],
                stdout=fotmp, stderr=fotmp)
        os.close(fdtmp)
        os.remove(stdoutfile)
    else:
        print "Counting objects in "+filename
        subprocess.check_call(
            [sex_exec, filename, "-c", config_filename, "-CATALOG_NAME", catfile], close_fds=True)
    data = pyfits.getdata(catfile)
    os.remove(catfile)
    return data

def count_all(root_dir, experiments=constants.experiments, obs_types=constants.obs_types,
              shear_types=constants.shear_types):
    """Check (including detection) objects in all FITS files in branches for the experiments,
    obs_types and shear_types specified,  within the specified root directory.

    Assumes all FITS files end in suffix .fits.

    @return good  If all checks pass, returns a dictionary containing the object totals that were
                  counted by this tool, itemized by the filename.  Any files
                  found to contain neither 9 or 10 0000 objects (for star fields and galaxy fields,
                  respectively) are judged as failed.  All failed filenames are printed and the
                  function raises a ValueError exception with all the failed filenames listed in the
                  error message.
    """
    # Set storage lists
    good = {}
    bad = {}
    found = {}
    for experiment in experiments:

        for obs_type in obs_types:

            for shear_type in shear_types:

                # Check for all files matching *.fits
                mapper = great3sims.mapper.Mapper(root_dir, experiment, obs_type, shear_type)
                fitsfiles = glob.glob(os.path.join(mapper.full_dir, "*.fits"))
                # If any fits files found, check
                if len(fitsfiles) > 0:
                    if experiment not in found:
                        found[experiment] = {}
                        if obs_type not in found[experiment]:
                            found[experiment][obs_type] = {}
                            if shear_type not in found[experiment][obs_type]:
                                found[experiment][obs_type][shear_type] = True
                                print "Counting objects in FITS files in "+str(mapper.full_dir)
                                for fitsfile in fitsfiles:

                                    if "image" in fitsfile:
                                        if obs_type == "space":
                                            config_filename = "sex_space.config"
                                        else:
                                            config_filename = "sex.config"
                                        print "Using "+config_filename
                                        data = file_count(fitsfile, config_filename=config_filename)
                                        nobs = len(data)
                                        if nobs == 9 and "starfield" in fitsfile:
                                            good[fitsfile] = {"nobs": nobs, "data": data}
                                        elif nobs == 10000:
                                            good[fitsfile] = {"nobs": nobs, "data": data}
                                        else:
                                            bad[fitsfile] = {"nobs": nobs, "data": data}
 
    print "Ran SExtractor on all FITS files in "+root_dir
    print "Verified object totals in FITS files for the following branches: \n"+str(found)
    print "Verified "+str(len(good))+"/"+str(len(good) + len(bad))+" FITS files by counting"
    if len(bad) > 0:
        message = "The following files failed FITS object counting:\n"
        for filename, entry in bad.iteritems():

            message += filename+" with "+str(entry["nobs"])+" objects\n" 

        print message
    else:
        print "All files verified successfully!"
    return good, bad


if __name__ == "__main__":

    import time
    import cPickle
    from sys import argv

    # Check the argument list length
    if len(argv) == 2:
        experiment = argv[1]
    else:
        import sys
        print "usage: ./count_objects.py EXPERIMENT"
        sys.exit(1)

    if not os.path.isdir("./counts"): os.mkdir("./counts") # Build the required directory
    # Loop over exps and obs making dictionary (lump both constant/variable together as detection
    # should not differ between these sets)
    for obs_type in constants.obs_types:

        good_public, bad_public = count_all(
            constants.public_dir, experiments=[experiment,], obs_types=[obs_type,])
        with open(
            os.path.join(
                "./counts",
                "goodcounts_"+experiment+"-"+obs_type+"_"+(time.asctime()).replace(" ", "_")+".p"),
            "wb") as fgood:
            print "Writing good dictionary to "+fgood.name
            cPickle.dump(good_public, fgood)
        with open(
            os.path.join(
                "./counts",
                "badcounts_"+experiment+"-"+obs_type+"_"+(time.asctime()).replace(" ", "_")+".p"),
            "wb") as fbad:
            print "Writing bad dictionary to "+fbad.name
            cPickle.dump(bad_public, fbad)

