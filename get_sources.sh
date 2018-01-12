#!/bin/bash
source sources.cfg
echo "Checking vixen..."
if [[ ! -e SOURCES/$VIXEN_FILE ]] ; then
    echo "Cloning vixen repo..."
    mkdir -p git-tmp
    pushd git-tmp

    git clone $VIXEN_URL vixen.git || exit 1
    cd vixen.git
    echo "Creating $VIXEN_FILE..."
    git archive --prefix=xen-vixen/ -o ../../SOURCES/$VIXEN_FILE $VIXEN_CSET || exit 1
    popd
fi

if [[ -e git-tmp ]] ; then
    echo "Cleaning up cloned repositores"
    rm -rf git-tmp
fi

echo "All sources present."
