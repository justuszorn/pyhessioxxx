

OPTIONS="-DCTA -DCTA_MAX_SC -g -O2 -Wall -D_LARGEFILE64_SOURCE -fPIC -DPIC -lm"

echo "build hessio library"
cd hessioxxx
mkdir bin out lib
make  CDEBUGFLAGS="-g -O2" DEFINES="-DCTA -DCTA_MAX_SC"
cd ..


echo "build pyhessio library"

echo "gcc -o pyhessio.so -Ihessioxxx/include -I. ${OPTIONS}  -shared pyhessio.c -L hessioxxx/lib -lhessio"
gcc -o pyhessio.so -Ihessioxxx/include -I.  ${OPTIONS}  -shared pyhessio.c -L hessioxxx/lib -lhessio
