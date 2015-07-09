# Jean Jacquemier
# IN2P3
# contact jacquem@lapp.in2p3.fr


1/ build hessio and pyhessio libraries
prompt%> ./build.sh

2/ Prepare system environment
prompt%> export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:hessioxxx/lib

3/ Execute test file
prompt%> python test.py -h
or
prompt%> python test.py -f ~/Downloads/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz --tel 4 --pix 40 --plot


