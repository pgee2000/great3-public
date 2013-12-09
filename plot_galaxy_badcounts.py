#!/usr/bin/env python

# usage: ./plot_galaxy_badcounts.py DICTFILE
import os
from sys import argv
import cPickle
import pyfits
import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":

    if len(argv) != 2:
        print "usage: ./plot_galaxy_badcounts.py DICTFILE"
        import sys
        sys.exit(1)
    # List for storing object counts 
    nobs = []
    # Setup a couple of variables to get the largest nobs
    biggest_nobs = 0
    biggest_nobs_field = ""
    baddict = cPickle.load(open(argv[1]))
    for key, subdict in baddict.iteritems():

        nobs.append(subdict["nobs"])
        if nobs[-1] > biggest_nobs:
            biggest_nobs = nobs[-1]
            biggest_nobs_field = key

    # Then plot the hist
    plt.hist(
        nobs, bins=50,
        label="Worst offender: "+os.path.split(biggest_nobs_field)[-1]+" with "+str(biggest_nobs))
    plt.xlabel("N objects")
    plt.legend()
    splitname = ((argv[1]).rsplit("_"))
    plt.title("Fields in "+str(splitname[1])+" with N objects != 10000")
    outfile = "histogram_"+((argv[1]).rstrip(".p"))+".png"
    print "Saving plot to "+outfile
    plt.savefig(outfile)
    plt.show()
     

