# verified on Fedora 18 / x86_64 2013-06-09

%ifnarch s390 s390x
%global with_openmpi 1
%else
%global with_openmpi 0
%endif

# to find the proper location for installing the lammps.py* files
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

Name:           lammps
Version:        20130609
Release:        1%{?dist}
Summary:        LAMMPS Molecular Dynamics Simulator
Group:          Applications/Engineering

License:        GPLv2
URL:            http://lammps.sandia.gov
Source0:        lammps-current.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  gcc-gfortran
BuildRequires:  fftw-devel
BuildRequires:  libjpeg-devel
Requires:       lammps-common = %{version}-%{release}

%global lammps_desc \
LAMMPS is an acronym for Large-scale Atomic/Molecular Massively Parallel\
Simulator. LAMMPS has potentials for soft materials (biomolecules, polymers)\
and solid-state materials (metals, semiconductors) and coarse-grained or\
mesoscopic systems. It can be used to model atoms or, more generically,\
as a parallel particle simulator at the atomic, meso, or continuum scale.\
LAMMPS runs on single processors or in parallel using message-passing\
techniques and a spatial-decomposition of the simulation domain, as well\
as using multi-threading via OpenMP inside each simulation domain.

%description
%{lammps_desc}

This package contains a LAMMPS executable compiled without MPI support.

%package common
Summary:        LAMMPS utilities and documentation
Group:          Applications/Engineering

%description common
%{lammps_desc}

This package contains common utilities and the documentation 



%if %{with_openmpi}
%package openmpi
Summary:        LAMMPS OpenMPI executable
Group:          Applications/Engineering
Requires:       lammps-common
Requires:       openmpi
BuildRequires:  openmpi-devel

%description openmpi
%{lammps_desc}

This package contains a parallel LAMMPS executable for OpenMPI.
%endif

%package mpich2
Summary:        LAMMPS MPICH2 executable
Group:          Applications/Engineering
Requires:       lammps-common
Requires:       mpich2
BuildRequires:  mpich2-devel

%description mpich2
%{lammps_desc}

This package contains a parallel LAMMPS executable for MPICH2.

%package python
Summary:        LAMMPS Python module
Group:          Applications/Engineering
Requires:       lammps-common
Requires:       python
BuildRequires:  python-devel

%description python
%{lammps_desc}

This package contains the LAMMPS Python module

%prep
%setup -q -n lammps-current

%build
# build supporting libraries for MPI stubs
cd lib/atc
make -f Makefile.g++ CC=g++ CCFLAGS="-fPIC -I../../src -I../../src/STUBS  ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.linalg
cd ../awpmd
make -f Makefile.openmpi CC=g++ CCFLAGS="-fPIC -Isystems/interact/TCP/ -Isystems/interact -Iivutils/include ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.linalg
cd ../colvars
make -f Makefile.g++ CXX=g++ CXXFLAGS="-fPIC ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.empty
cd ../linalg
make -f Makefile.gfortran FC=gfortran FFLAGS="-fPIC ${RPM_OPT_FLAGS}" FFLAGS0="${RPM_OPT_FLAGS} -O0 -fPIC"
cd ../meam
make -f Makefile.gfortran F90=gfortran F90LAGS="-fPIC ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.gfortran
cd ../poems
make -f Makefile.g++ CC=g++ CCFLAGS="-fPIC ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.empty
cd ../voronoi
make -f Makefile.g++ CXX=g++ CXXFLAGS="-fPIC ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.empty

# now build in main source directory
cd ../../src

# install packages
# fortran reax is obsolete, no GPU support.
make yes-all no-kim no-gpu no-user-cuda no-reax

make -C STUBS

make g++ CC=g++ CCFLAGS="${RPM_OPT_FLAGS} -fopenmp -fPIC" LINK=g++ LINKFLAGS="${RPM_LD_FLAGS} -fopenmp" LMP_INC="-DLAMMPS_GZIP -DLAMMPS_JPEG" MPI_INC="-I../STUBS" MPI_PATH="-L../STUBS" MPI_LIB=-lmpi_stubs FFT_INC=-DFFT_FFTW3 FFT_LIB=-lfftw3 JPG_LIB=-ljpeg

# build shared library for python bindings
mv Obj_g++ Obj_shlib_g++
make makeshlib
make -f Makefile.shlib g++ CC=g++ CCFLAGS="${RPM_OPT_FLAGS} -fopenmp" LINK=g++ LINKFLAGS="${RPM_LD_FLAGS} -fopenmp" LMP_INC="-DLAMMPS_GZIP -DLAMMPS_JPEG" MPI_INC="-I../STUBS" MPI_PATH="-L../STUBS" MPI_LIB=-lmpi_stubs FFT_INC=-DFFT_FFTW3 FFT_LIB=-lfftw3 JPG_LIB=-ljpeg
mv Obj_shlib_g++ Obj_g++

# stash executable and shared lib away
cd ../
mkdir serial
mv src/lmp_g++ serial/
mv src/liblammps_g++.so serial/liblammps.so

# byte compile python script wrapper
cd python
ln -s ../serial/liblammps.so
cat > dummy.py <<EOF
from lammps import lammps
lmp = lammps()
EOF
LD_LIBRARY_PATH=.:${LD_LIBRARY_PATH} %{__python} -O dummy.py
cd ../

# now build some tools
g++ -o serial/restart2data ${RPM_OPT_FLAGS} tools/restart2data.cpp
g++ -o serial/binary2txt ${RPM_OPT_FLAGS} tools/binary2txt.cpp
gfortran -o serial/chain.x ${RPM_OPT_FLAGS} tools/chain.f

# build OpenMPI parallel version, if supported
%if %{with_openmpi}
%{_openmpi_load}
# need to rebuild lib/atc
cd lib/atc
make -f Makefile.g++ clean
make -f Makefile.g++ CC=mpicxx CCFLAGS="-fPIC -I../../src -DMPICH_IGNORE_CXX_SEEK -DOMPI_SKIP_MPICXX=1 ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.linalg

# back to main source dir
cd ../../src
make clean-g++

make g++ CC=mpicxx CCFLAGS="${RPM_OPT_FLAGS} -fopenmp" LINK=mpicxx LINKFLAGS="${RPM_LD_FLAGS} -fopenmp" LMP_INC="-DLAMMPS_GZIP -DLAMMPS_JPEG" MPI_INC="" MPI_PATH="" MPI_LIB="" FFT_INC=-DFFT_FFTW3 FFT_LIB=-lfftw3 JPG_LIB=-ljpeg

# and save the executable
cd ../
mkdir openmpi
mv src/lmp_g++ openmpi/
%{_openmpi_unload}
%endif

# build MPICH2 parallel version
%{_mpich2_load}
# need to rebuild lib/atc
cd lib/atc
make -f Makefile.g++ clean
make -f Makefile.g++ CC=mpicxx CCFLAGS="-fPIC -I../../src -DMPICH_IGNORE_CXX_SEEK -DOMPI_SKIP_MPICXX=1 ${RPM_OPT_FLAGS}" EXTRAMAKE=Makefile.lammps.linalg

# back to main source dir
cd ../../src
make clean-g++

make g++ CC=mpicxx CCFLAGS="${RPM_OPT_FLAGS} -fopenmp" LINK=mpicxx LINKFLAGS="${RPM_LD_FLAGS} -fopenmp" LMP_INC="-DLAMMPS_GZIP -DLAMMPS_JPEG" MPI_INC="" MPI_PATH="" MPI_LIB="" FFT_INC=-DFFT_FFTW3 FFT_LIB=-lfftw3 JPG_LIB=-ljpeg

# and save the executable
cd ../
mkdir mpich2
mv src/lmp_g++ mpich2/
%{_mpich2_unload}

# build done (so far)

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
install -p -m 755 serial/lmp_g++ %{buildroot}%{_bindir}
install -p -m 755 serial/restart2data %{buildroot}%{_bindir}
install -p -m 755 serial/binary2txt %{buildroot}%{_bindir}
install -p -m 755 serial/chain.x %{buildroot}%{_bindir}

%if %{with_openmpi}
%{_openmpi_load}
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/openmpi/bin
install -p -m 755 openmpi/lmp_g++ $RPM_BUILD_ROOT/%{_libdir}/openmpi/bin/
%{_openmpi_unload}
%endif

%{_mpich2_load}
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/mpich2/bin
install -p -m 755 mpich2/lmp_g++ $RPM_BUILD_ROOT/%{_libdir}/mpich2/bin/
%{_mpich2_unload}

mkdir -p $RPM_BUILD_ROOT/%{python_sitearch}
mkdir -p $RPM_BUILD_ROOT/%{_libdir}
cp python/lammps.py* $RPM_BUILD_ROOT/%{python_sitearch}
cp serial/liblammps.so $RPM_BUILD_ROOT/%{_libdir}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{_bindir}/lmp_g++

%files common
%defattr(-,root,root,-)
%{_bindir}/restart2data
%{_bindir}/binary2txt
%{_bindir}/chain.x
%doc README LICENSE doc/Manual.pdf bench potentials

%if %{with_openmpi}
%files openmpi
%defattr(-,root,root,-)
%{_libdir}/openmpi/bin/lmp_g++
%endif

%files mpich2
%defattr(-,root,root,-)
%{_libdir}/mpich2/bin/lmp_g++

%files python
%defattr(-,root,root,-)
%doc python/README python/examples
%{python_sitearch}/*
%{_libdir}/liblammps.so


%changelog
* Sun Jun  9 2013 Axel Kohlmeyer <akohlmey@gmail.com> - 20130609-1
- Added subpackage for python wrapper

* Sun Jun  9 2013 Axel Kohlmeyer <akohlmey@gmail.com> - 20130609-1
- Initial Fedora/RedHat style SPEC file

