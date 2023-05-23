default: all
.PHONY: all treeOclock seidel

all : spr_path.so rss_distance.so treeOclock seidel

spr_path.so: treeOclock seidel spr_path.o
	gcc -shared -o spr_path.so treeOclock/tree.o treeOclock/rnni.o treeOclock/spr.o seidel_compressed/libseidel.so spr_path.o

spr_path.o: spr_path.c spr_path.h
	gcc -fPIC -Wall -c -g -O2 spr_path.c

rss_distance.so: treeOclock seidel rss_distance.o
	gcc -shared -o rss_distance.so treeOclock/tree.o treeOclock/rnni.o treeOclock/spr.o seidel_compressed/libseidel.so rss_distance.o

rss_distance.o: rss_distance.c rss_distance.h
	gcc -fPIC -Wall -c -g -O2 rss_distance.c

treeOclock:
	make -C treeOclock

seidel:
	make -C seidel_compressed
