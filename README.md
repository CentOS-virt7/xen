# Branches

 - `xen-48` is the branch for Xen 4.8 (currently supported)
 - `xen-410` is the branch for Xen 4.10
 - `xen-412` is the branch for Xen 4.12

# repo script

The main directory has a script called `repo` with a number of
'utility' functions.  A quick summary can be found by running `./repo
help`.

None of these functions call `sudo`; the content
can be found in `lib/*.sh`, and configuration for current version, &c can
be found in `sources.cfg`.

# Building

The first thing to do, after checking out the appropriate branch, is
to get the required source files.  Do this by running the included
script:

    ./repo get-sources

Then do an `rpmbuild` (obviously replacing `el7` with `el6` for CentOS 6):

    rpmbuild --define "_topdir $PWD" --define "dist .el7" -bb SPECS/*.spec

Or, make an srpm and submit it to koji:

    rpmbuild --define "_topdir $PWD" --define "dist .el7" -bs SPECS/*.spec

    cbs build virt7-xen-46-el7 SRPMS/*.el7.src.rpm

# Adding qemu patches

Add qemu patches the normal way: by copying the patches to `SOURCES`,
adding a `PatchNN:` line to the `xen.spec` file, and then adding
`%patchNN -p1` in the appropriate place in the file file.

For the 'NN', we use the following number sequence for patches:
* 1000+: blktap
* 3000+: qemu-xen-traditional

Take XSA-130 for example; this had two patches, `xsa130-qemuu.patch`,
and `xsa130-qemut.patch`, for qemu-xen ("qemu upstream") and
qemu-traditional, respectively.  To add those patches do the
following:

Copy them into `SOURCES`, and then add them to git:

    cp  /path/to/xsas/xsa130-qemu*.patch SOURCES/

Then add the following two lines in the "Patch" section:

    Patch3001: xsa130-qemut.patch

And finally, add the following line after `pushd tools/qemu-xen-traditional`:

    %patch3001 -p1

# Working with the Xen patchqueue

The core Xen patchqueue is stored as a `git` "am" file.  This makes it a
tiny bit more difficult to add a single patch, but makes it *much*
easier to work with when it comes to rebasing to a new version of Xen.

Most of these operations are implemented in the `repo` script; a
breakdown of what's going on inside is included to help understanding.
To work with the script requires that you have both `git` and stackgit
(`stg`) installed.

## Making a git tree with the patchqueue

Start by cloning the upstream git repository:

    ./repo make-tree

This will create a tree in `UPSTREAM/xen.git` based on the
`XEN_VERSION` set in `sources.cfg`.  Suppose that `XEN_VERSION` is set
to `4.6.0`. `make-tree` will make the following branches:

 - `base/4.6.0`: A branch based on `RELEASE-4.6.0`

 - `centos/pq/4.6.0`: A branch based on the above, but with the
   CentOS "patchqueue" (`SOURCES/xen-queue.am`) applied.

To do this manually:

    mkdir UPSTREAM
    cd UPSTREAM
    git clone git://xenbits.xenproject.org/xen.git xen.git
    cd xen.git

Check out the appropriate release tag:

    git checkout -b 4.6.0 RELEASE-4.6.0

Now create a stackgit branch for the patches:

    stg branch --create centos/pq/4.6.0

And import the patchqueue:

    stg import -M ${path_to_package_repo}/SOURCES/xen-queue.am

## Importing patches to the patchqueue

Once you have the tree, you can import new patches to the queue like this:

    ./repo import-patches /path/to/xsas/xsa150.patch

Once you've imported all the patches and everything works, update
`SOURCES/xen-queue.am` like this:

    ./repo sync-queue

Or to do the above manually, from the `UPSTREAM/xen.git` repo:

    stg import -m /path/to/xsas/xsa150.patch

When you're done, export the patchqueue back to `xen-queue.am`:

    git format-patch --stdout -N RELEASE-4.6.0 > ${path_to_package_repo}/SOURCES/xen-queue.am

And finally, run the script provided in this repo to remove extraneous
information from the patchqueue (such as the version of git you're
running) and reduce the diff size:

    ./pqnorm.pl


## Rebasing to a new version of Xen

Suppose you 4.6.1 comes out, and you want to rebase the patchqueue.
Assuming you took my advice above, you already have the patchqueue in
stg format from above.

You can start the process as follows:

    ./repo rebase new=4.6.1

This will create `base/4.6.1` and `centos/pq/4.6.1`, and begin
rebasing the existing patchqueue.  This rarely succeeds completely the
first time; you'll have to manually fix up the process (often by
removing old XSAs).  After fixing things up, finish the process by
running

    ./repo rebase-post

This will sync the patchqueue, as well as updating `XEN_VERSION` in
`sources.cfg`.  You'll have to update `xen.spec` (see below) and call
`get-sources` to fetch the new tarball.

To do it manually, first clone the entire patchqueue (so you have a
backup in case things go wrong):

    git checkout centos/pq/4.6.0
    stg branch --clone centos/pq/4.6.1

Then rebase to the new version, checking for merged patches:

    stg rebase -m RELEASE-4.6.1

Many of the patches may fail to apply, in which case you'll need to do
through the process of fixing them up and doing `stg refresh`, then
repeating with `stg push -a` until they all apply.

Patches which already exist in upstream (for instance, XSAs) will
automatically be turned into empty patches; you can have stackgit get
rid of these like this:

    stg clean

Now export the patchqueue:

    git format-patch --stdout -N RELEASE-4.6.1 > ${path_to_package_repo}/SOURCES/xen-queue.am

Clean it up:

    ./pqnorm.pl

Update `get_sources.sh` with the new version:

    XEN_VERSION=4.6.1

And run it again to fetch the new version (and make sure it still works properly):

    ./repo get-sources

Update `SPECS/xen.spec` with the new version and changelog, and build.

You may need to remove qemu-related patches from `xen.spec` as well
(See "Adding qemu patches" for more information.)

## Updating your xen.git tree based on updates to this repo

Suppose someone else pushes some changes to CentOS-virt7/xen that
modifies the patchqueue.  To update your tree:

    ./repo sync-tree

Or do it manually:

    git checkout base/4.6.1
    stg branch --delete --force centos/pq/4.6.1
    stg branch --create centos/pq/4.6.1
    stg import -M ../../SOURCES/xen-queue.am

