#!/bin/bash
source sources.cfg
echo "Checking Xen $XEN_VERSION release tarball"
if [[ ! -e SOURCES/$XEN_RELEASE_FILE ]] ; then
    wget -P SOURCES/ $XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE || exit 1
fi
if gpg --list-keys 0x${XEN_KEY}; then
    if [[ ! -e SOURCES/$XEN_RELEASE_FILE.sig ]]; then
        wget -P SOURCES/ $XEN_RELEASE_BASE/$XEN_VERSION/$XEN_RELEASE_FILE.sig || exit 1
    fi
    gpg --status-fd 1 --verify SOURCES/$XEN_RELEASE_FILE.sig SOURCES/$XEN_RELEASE_FILE \
      | grep -q "GOODSIG ${XEN_KEY}" || exit 1
else
    echo "Not checking gpg signature due to missing key; add with gpg --recv-keys ${XEN_KEY}"
fi
echo "Checking external sources: "
for i in $XEN_EXTLIB_FILES ; do
    echo " checking $i"
    if [[ ! -e SOURCES/$i ]] ; then
	wget -P SOURCES/ $XEN_EXTLIB_URL/$i || exit 1
    fi
done

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
