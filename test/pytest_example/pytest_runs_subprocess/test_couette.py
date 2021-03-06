import pytest
import os
import sys
import numpy as np
import subprocess as sp
from OpenFOAM_vs_analytical import check_OpenFOAM_vs_Analytical


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

# Import symwraplib
sys.path.insert(0, "./SimWrapPy/")
try:
    import simwraplib as swl
except ImportError:
    cmd = "git clone https://github.com/edwardsmith999/SimWrapPy.git ./SimWrapPy"
    downloadout = sp.check_output(cmd, shell=True)
    print(downloadout)
    sys.path.insert(0, "./SimWrapPy")
    import simwraplib as swl

#Define test directory based on script file
TEST_DIR = os.path.dirname(os.path.realpath(__file__))

#Parameterise range of cases
params = []
Uwall = [0.2, 0.5, 1.0, 2.0]
for exe in ["CPLSediFOAM", "CPLCFDDEMFoam"]:
    for u in Uwall:
        params.append([u, exe])
@pytest.mark.parametrize("wallvel, executable", params)
def test_newtest(wallvel, executable):

    # Inputs that are the same for every thread
    basedir = TEST_DIR
    srcdir = None
    inputfile = "/openfoam"
    rundir = TEST_DIR + "/run" + str(wallvel)

    #Clean previous result, generate grid and decompose for parallel run
    with cd (TEST_DIR+"/"+inputfile):
        sp.check_output("python clean.py -f", shell=True)
        sp.check_output("blockMesh", shell=True)
        sp.check_output("decomposePar", shell=True)

    #Setup Changes
    keyvals = {"boundaryField":{"top":{"type":"fixedValue", "value":[[wallvel,0,0]]}, 
                                "bottom":{"type":"keep", "value":"keep"},
                                "streamwiseIn":{"type":"keep", "neighbourPatch":"keep"},
                                "streamwiseOut":{"type":"keep", "neighbourPatch":"keep"},
                                "front":{"type":"keep", "neighbourPatch":"keep"},
                                "back":{"type":"keep", "neighbourPatch":"keep"}}}
    changes = {"Ub":keyvals}

    with cd(TEST_DIR):

        #Setup a LAMMPS run object
        of = swl.OpenFOAMRun(None, basedir, rundir,
                             executable, inputfile,
                             inputchanges=changes)

        #Setup a mock script
        mockscript = "./python_dummy/test_vs_couette_analytical.py"
        mock = swl.ScriptRun(rundir, mockscript, inputchanges={"U = ": wallvel})

        #Setup a coupled run
        run = swl.CPLRun(None, basedir, rundir, [mock, of],
                         inputfile="/cpl/COUPLER.in")

        #Run the case
        run.setup()
        run.execute(blocking=True, print_output=True, extra_cmds="-M")

        #Seems that blocking is not working correctly, add a wait here to see if the problem is simply this
        #import time
        #time.sleep(10)

        #Check results are correct
        check_OpenFOAM_vs_Analytical(rundir)

            
