SWIG=swig
SWIGFLAGS=-python -c++
WGET=wget -q

CC=g++
CPPFLAGS=-fPIC -O3
INCLUDEPATH=/usr/include/python3.6

cpp: _model.so model.py

%.py: %.i
	$(SWIG) $(SWIGFLAGS) -o $@ $<

%_wrap.cpp: %.i numpy.i
	$(SWIG) $(SWIGFLAGS) -o $@ $<

%.o: %.cpp
	$(CC) $(CPPFLAGS) -I $(INCLUDEPATH) -c $< -o $@

_%.so: %.o %_wrap.o
	$(CC) -shared $^ -o $@

%.i:
	$(WGET) "https://raw.githubusercontent.com/numpy/numpy/master/tools/swig/numpy.i"
