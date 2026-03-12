FROM ubuntu:20.04


SHELL ["/bin/bash", "-c"] 

RUN useradd -ms /bin/bash pulsarx

ENV DEBIAN_FRONTEND noninteractive
ENV HOME /home/pulsarx

ENV LD_LIBRARY_PATH=$HOME/software/lib:/usr/local/lib:$LD_LIBRARY_PATH
ENV YMW16_DIR=$HOME/software/XLibs/src/ymw16
ENV PATH=$PATH:$HOME/software/bin:$HOME/.local/bin
ENV OMP_NUM_THREADS=1
ENV PSRCAT_FILE=/home/pulsarx/software/psrcat_tar/psrcat.db
ENV TEMPO2=/home/pulsarx/software/tempo2/T2runtime
ENV PGPLOT_DIR=$HOME/software/pgplot
ENV PGPLOT_FONT=$PGPLOT_DIR/grfont.dat

USER root

RUN apt-get update

RUN apt-get install -y git \
    autoconf \
    libtool \
    g++ \
    gfortran \
    libboost-program-options-dev \
    libboost-log-dev \
    libcfitsio-dev \
    libblas-dev \
    liblapack-dev \
    libeigen3-dev \
    libpng-dev \
    libfftw3-dev \
    pgplot5 \
    wget \
    make \
	cmake \
	mpich \
    libx11-dev \
	python3-pip \
    python3-dev \
    python3-distutils \
    python3-numpy \
	python3-scipy \
    python3-matplotlib

#--- tempo2 --- 
WORKDIR $HOME/software
RUN git clone https://bitbucket.org/psrsoft/tempo2.git
WORKDIR $HOME/software/tempo2
RUN rm -rf .git
RUN ./bootstrap
RUN ./configure --prefix=$HOME/software
RUN make -j 8 && make install
RUN make plugins-install
RUN make clean

# --- PSRCHIVE ---
# WORKDIR $HOME/software
# RUN git clone https://github.com/rossjjennings/psrchive.git
# WORKDIR $HOME/software/psrchive
# RUN ./bootstrap
# RUN ./configure 
# RUN make -j$(nproc)

# --- MultiNest ---
WORKDIR $HOME/software
RUN git clone https://github.com/JohannesBuchner/MultiNest.git
WORKDIR $HOME/software/MultiNest/build
RUN cmake -DCMAKE_PREFIX_PATH=$HOME/software ..
RUN make && make install

RUN pip3 install mpi4py
RUN pip3 install pybind11
RUN pip3 install pyyaml
RUN pip3 install joblib
RUN pip3 install scienceplots

WORKDIR $HOME/software
RUN git clone https://github.com/JohannesBuchner/PyMultiNest/
WORKDIR $HOME/software/PyMultiNest
RUN python3 setup.py install

# --- sofa ---
WORKDIR $HOME/software
RUN git clone https://github.com/liberfa/erfa.git
WORKDIR $HOME/software/erfa
RUN ./bootstrap.sh
RUN ./configure --prefix=$HOME/software
RUN make -j 8 && make install

# --- psrcat --- 
WORKDIR $HOME/software
RUN wget https://www.atnf.csiro.au/research/pulsar/psrcat/downloads/psrcat_pkg.tar.gz && \
    tar -zxvf psrcat_pkg.tar.gz
WORKDIR $HOME/software/psrcat_tar
RUN source makeit && cp psrcat $HOME/software/bin

WORKDIR $HOME/software
RUN git clone https://github.com/ypmen/PlotX.git
RUN git clone https://github.com/ypmen/XLibs.git
RUN git clone https://github.com/ypmen/PulsarX.git
RUN git clone https://github.com/ypmen/BasebandX.git
RUN git clone https://github.com/OwenJohnsons/TransientX.git

# --- PlotX ---
RUN apt-get install -y libcpgplot0 
RUN apt-get install -y libquadmath0
ENV PGPLOT_DIR=/usr/lib/pgplot5
ENV PGPLOT_FONT=/usr/lib/pgplot5/grfont.dat
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH
WORKDIR $HOME/software/PlotX
RUN ./bootstrap
RUN ./configure --prefix="$HOME/software" LDFLAGS="-L/usr/lib" CPPFLAGS="-I/usr/include" LIBS="-lpgplot -lcpgplot -lX11"
RUN make -j 8 && make install
RUN make clean

WORKDIR $HOME/software/XLibs
RUN ./bootstrap
RUN ./configure --prefix=$HOME/software CXXFLAGS="-std=c++11 -O3" LDFLAGS="-L$HOME/software/lib" CPPFLAGS="-I$HOME/software/include" LIBS="-lpgplot -lcpgplot -lX11"
RUN make -j 8 && make install
RUN make clean

WORKDIR $HOME/software/BasebandX
RUN ./bootstrap
RUN ./configure --prefix=$HOME/software CXXFLAGS="-std=c++11 -O3" LDFLAGS="-L$HOME/software/lib" CPPFLAGS="-I$HOME/software/include" LIBS="-lpgplot -lcpgplot -lX11"
RUN make -j 8 && make install
RUN make clean

WORKDIR $HOME/software/TransientX
RUN ./bootstrap
RUN ./configure --prefix=$HOME/software CXXFLAGS="-std=c++11 -O3" LDFLAGS="-L$HOME/software/lib" CPPFLAGS="-I$HOME/software/include"
RUN make -j 8 && make install
RUN make clean

USER root
WORKDIR $HOME/software/PulsarX/python
RUN python3 setup.py install
USER pulsarx

WORKDIR $HOME/software
RUN pip3 install pyyaml
RUN pip3 install mpi4py
RUN pip3 install pybind11

USER root
WORKDIR $HOME/software/PulsarX/python
RUN python3 setup.py install

USER pulsarx
WORKDIR $HOME/software
CMD ["/bin/sh"] 