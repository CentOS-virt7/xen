# Branches

`xen-44` is the branch for Xen 4.4.  `xen-46` is the branch for Xen 4.6.

# Building

The first thing to do, after checking out the appropriate branch, is
to get the required source files.  Do this by running the included
script:

    ./get_sources.sh

Then do an `rpmbuild` (obviously replacing `el7` with `el6` for CentOS 6):

    rpmbuild --define "_topdir $PWD" --define "dist .el7" -bb SPECS/*.spec

Or, make an srpm and submit it to koji:

    rpmbuild --define "_topdir $PWD" --define "dist .el7" -bs SPECS/*.spec

    koji build virt7-xen-46-el7 SRPMS/*.el7.src.rpm

# Adding qemu patches

Add qemu patches the normal way: by copying the patches to `SOURCES`,
adding a `PatchNN:` line to the `xen.spec` file, and then adding
`%patchNN -p1` in the appropriate place in the file file.

For the 'NN', we use the following number sequence for patches:
* 1000+: blktap
* 2000+: qemu-xen
* 3000+: qemu-xen-traditional

Take XSA-130 for example; this had two patches, `xsa130-qemuu.patch`,
and `xsa130-qemut.patch`, for qemu-xen ("qemu upstream") and
qemu-traditional, respectively.  To add those patches do the
following:

Copy them into `SOURCES`, and then add them to git:

    cp  /path/to/xsas/xsa130-qemu*.patch SOURCES/

Then add the following two lines in the "Patch" section:

    Patch2001: xsa130-qemuu.patch

    Patch3001: xsa130-qemut.patch

And finally, add the the following line after `pushd tools/qemu-xen`:

    %patch2001 -p1

And the following line after `pushd tools/qemu-xen-traditional`:

    %patch3001 -p1

# Working with the Xen patchqueue

The core Xen patchqueue is stored as a git "am" file.  This makes it a
tiny bit more difficult to add a single patch, but makes it *much*
easier to work with when it comes to rebasing to a new version of Xen.

I strongly encourage you to use "stackgit" for working with this
queue, as it makes things much easier.  (If you've used quilt, the
concepts are somewhat similar.)

Start by cloning the upstream git repository somewhere:

    git clone git://xenbits.xenproject.org/xen.git xen.git
    cd xen.git

Check out the appropriate release tag:

    git checkout -b 4.6.0 RELEASE-4.6.0

Now create a stackgit branch for the patches:

    stg branch --create centos/pq/4.6.0

And import the patchqueue:

    stg import -M ${path_to_package_repo}/SOURCES/xen-queue.am

Now you can manipulate the patchqueue using normal stackgit commands.
For example, if you wanted to import the patch from XSA-150:

    stg import /path/to/xsas/xsa150.patch

When you're done, export the patchqueue back to `xen-queue.am`:

    git format-patch --stdout -N RELEASE-4.6.0 > ${path_to_package_repo}/SOURCES/xen-queue.am

I also strongly recommend keeping this tree around, so you can simply
manipulate it and then do the export again, rather than repeating the
whole process each time.

# Rebasing to a new version of Xen

Suppose you 4.6.1 comes out, and you want to rebase the patchqueue.
Assuming you took my advice above, you already have the patchqueue in
stg format from above.

First clone the entire patchqueue (so you have a backup in case things
go wrong):

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

Update `get_sources.sh` with the new version:

    XEN_VERSION=4.6.1

And run it again to fetch the new version (and make sure it still works properly):

    ./get_sources.sh

Update `SPECS/xen.spec` with the new version and changelog, and build.

You may need to remove qemu-related patches from `xen.spec` as well
(See "Adding qemu patches" for more information.)
