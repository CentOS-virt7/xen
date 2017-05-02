#!/bin/bash
XEN_VERSION=4.6.3
XEN_RELEASE_BASE=https://downloads.xenproject.org/release/xen/
XEN_RELEASE_FILE=xen-$XEN_VERSION.tar.gz
echo "Checking Xen $XEN_VERSION release tarball"
if [[ ! -e SOURCES/$XEN_RELEASE_FILE ]] ; then
    wget -P SOURCES/ $XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE || exit 1
fi

XEN_EXTLIB_URL=http://xenbits.xen.org/xen-extfiles
XEN_EXTLIB_FILES="grub-0.97.tar.gz \
	     lwip-1.3.0.tar.gz \
	     newlib-1.16.0.tar.gz \
	     pciutils-2.2.9.tar.bz2 \
	     polarssl-1.1.4-gpl.tgz \
	     zlib-1.2.3.tar.gz"
echo "Checking external sources: "
for i in $XEN_EXTLIB_FILES ; do
    echo " checking $i"
    if [[ ! -e SOURCES/$i ]] ; then
	wget -P SOURCES/ $XEN_EXTLIB_URL/$i || exit 1
    fi
done



BLKTAP_URL=https://github.com/xapi-project/blktap
BLKTAP_CSET=d73c74874a449c18dc1528076e5c0671cc5ed409
BLKTAP_FILE=blktap-$BLKTAP_CSET.tar.gz
echo "Checking blktap..."
if [[ ! -e SOURCES/$BLKTAP_FILE ]] ; then
    mkdir -p git-tmp
    pushd git-tmp
    
    echo " Cloning blktap repo..."
    git clone $BLKTAP_URL blktap.git || exit 1
    cd blktap.git
    echo " Creating $BLKTAP_FILE..."
    git archive --prefix=blktap2/ -o ../../SOURCES/$BLKTAP_FILE $BLKTAP_CSET || exit 1
    popd
fi

EDK2_URL=https://github.com/tianocore/edk2.git
EDK2_CSET=0cebfe81f94be36116af66d0a3134ce18d89eec1
EDK2_FILE=edk2-$EDK2_CSET.tar.gz
echo "Checking edk2 (tianocore)..."
if [[ ! -e SOURCES/$EDK2_FILE ]] ; then
    echo "Cloning tianocore repo..."
    mkdir -p git-tmp
    pushd git-tmp

    git clone $EDK2_URL edk2.git || exit 1
    cd edk2.git
    echo "Creating $EDK2_FILE..."
    git archive --prefix=edk2/ -o ../../SOURCES/$EDK2_FILE $EDK2_CSET || exit 1
    popd
fi

if [[ -e git-tmp ]] ; then
    echo "Cleaning up cloned repositores"
    rm -rf git-tmp
fi

echo "All sources present."
