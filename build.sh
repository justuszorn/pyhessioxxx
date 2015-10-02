OPTIONS="-DCTA -DCTA_MAX_SC -g -O2 -Wall -D_LARGEFILE64_SOURCE -fPIC -DPIC -lm"

echo "build hessio library"
cd hessioxxx
mkdir bin out lib
make  CDEBUGFLAGS="-g -O2" DEFINES="-DCTA -DCTA_MAX_SC"
cd ..

echo "build pyhessio library"
<<<<<<< HEAD
echo "gcc -o pyhessio.so -Ihessioxxx/include -I.  ${OPTIONS}  -shared pyhessio.c -L hessioxxx/lib -lhessio"
=======

echo "gcc -o pyhessio.so -Ihessioxxx/include -I. ${OPTIONS}  -shared pyhessio.c -L hessioxxx/lib -lhessio"
>>>>>>> ffc41477107b37820f50f8f7e64bb874046bf700
gcc -o pyhessio.so -Ihessioxxx/include -I.  ${OPTIONS}  -shared pyhessio.c -L hessioxxx/lib -lhessio
