#mpirun -np 27 python dummyMD_forces.py : -np 27 CPLIcoFoam -parallel -case test_forces_case
mpirun -n 27 python2 dummyMD_forces.py & PID=$!; mpirun -n 27 CPLIcoFoam -parallel -case test_forces_case ; wait $PID
reconstructPar -case test_forces_case
stressComponents -case test_forces_case
writeCellCentres -case test_forces_case
