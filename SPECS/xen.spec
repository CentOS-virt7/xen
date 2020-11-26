%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}



%define _libexecdir %{_libdir}

# build an efi boot image (where supported) unless rpmbuild was run with
# --without efi
%define build_efi %{?_without_efi: 0} %{?!_without_efi: 1}

# build with live patching enabled unless rpmbuild was run with
# --without livepatch
%define with_livepatch %{?_without_livepatch: 0} %{?!_without_livepatch: 1}

%if 0%{?centos_ver} == 6
%define with_sysv 1
%define with_systemd 0
%else
%define with_sysv 0
%define with_systemd 1
%endif

%define xen_efi_vendor Xen

%ifarch aarch64
%define with_ocaml 0
%define with_stubdom 0
%define with_blktap 0
%define with_spice 0
%define with_tianocore 1
%define build_efi 1
%else
%define with_ocaml  1
%define with_stubdom 1
%define with_blktap 1
# Provided by xen-ovmf package
%define with_tianocore 0
%if 0%{?centos_ver} <= 6
%define with_spice 0
%else
%define with_spice 1
%endif
# FIXME
%define build_efi 0
%endif

# Build ocaml bits unless rpmbuild was run with --without ocaml 
# or ocamlopt is missing (the xen makefile doesn't build ocaml bits if it isn't there)
%define build_ocaml %(test -x %{_bindir}/ocamlopt && echo %{with_ocaml} || echo 0)
# xen only supports efi boot images on x86_64



# Hypervisor ABI
%define hv_abi 4.10
%define xen_version %{hv_abi}.4

# Xen Project release candidates
# To build a package for a RC:
# - Set xen_rc_base to "rcX" (X been the RC release number)
# - Change the package Release number to "0.X" (X is incremented for every new
#   build of an RC package)
# - Version should be the version of Xen once released
# Once Xen is released:
# - Set xen_rc_base to 0
# - Change the package Release number to 1
%define xen_rc_base 0
%if %{xen_rc_base}
%define xen_rc_pkgver .%{xen_rc_base}
%define xen_rc -%{xen_rc_base}
%endif

# Snapshot from git tree
## Number of commit since the last stable tag
%define nb_commit 102
## Abbrev to 10 character of the commit id
%define abbrev_cset 17ec9b43af

%if %{nb_commit}
%define pkg_version %{xen_version}.%{nb_commit}.g%{abbrev_cset}
%define xen_tarball_dir xen-RELEASE-%{xen_version}-%{nb_commit}-g%{abbrev_cset}
%else
%define pkg_version %{xen_version}
%define xen_tarball_dir xen-%{xen_version}
%endif

Summary: Xen is a virtual machine monitor
Name:    xen
Version: %{pkg_version}
Release: 2%{?xen_rc_pkgver}%{?dist}
Group:   Development/Libraries
License: GPLv2+ and LGPLv2+ and BSD
URL:     https://www.xenproject.org/
Source0: %{xen_tarball_dir}.tar.gz
Source1: xen.modules
Source2: xen.logrotate
# used by stubdoms
%if %{with_stubdom}
Source10: lwip-1.3.0.tar.gz
Source11: newlib-1.16.0.tar.gz
Source12: zlib-1.2.3.tar.gz
Source13: pciutils-2.2.9.tar.bz2
Source14: grub-0.97.tar.gz
Source15: polarssl-1.1.4-gpl.tgz
%endif
# systemd bits
Source49: tmpfiles.d.xen.conf
%ifarch x86_64
Source50: xen-kernel.x86_64
%endif
%ifarch aarch64
Source51: xen-kernel.aarch64
%endif
%if %{build_efi}
Source52: efi-xen.cfg.aarch64
%endif
%if %{with_tianocore}
Source53: edk2-947f3737abf65fda63f3ffd97fddfa6986986868.tar.gz
%endif

%if %{with_livepatch}
Source60: livepatch-tools-0c104573a1c168995ec553778d1d2d1ebe9c9042.tar.gz
%endif

Source101: blktap-d73c74874a449c18dc1528076e5c0671cc5ed409.tar.gz

Patch1: xen-queue.am

# Out-of-tree patches.  
#
# Use the following patch numbers:
# 1000+: blktap
# 2000+: qemu-xen
# 3000+: qemu-traditional
Patch1001: xen-centos-disableWerror-blktap25.patch
Patch1005: xen-centos-blktap25-ctl-ipc-restart.patch
Patch1006: xsa155-centos-0002-blktap2-Use-RING_COPY_REQUEST-block-log-only.patch

# aarch64-only
%ifarch aarch64
Patch2001: qemuu-hw-block-xen-disk-WORKAROUND-disable-batch-map-when-.patch
%endif
Patch2002: xsa335-qemu.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: transfig libidn-devel zlib-devel texi2html SDL-devel curl-devel
BuildRequires: libX11-devel python-devel ghostscript texlive-latex
BuildRequires: ncurses-devel gtk2-devel libaio-devel libtool
# for the docs
BuildRequires: perl texinfo graphviz
%ifarch x86_64
# so that x86_64 builds pick up glibc32 correctly
BuildRequires: /usr/include/gnu/stubs-32.h
# for the VMX "bios"
BuildRequires: dev86
# build using Fedora ipxe packages for roms
BuildRequires: ipxe-roms-qemu
# iasl needed to build hvmloader
BuildRequires: iasl
%endif
BuildRequires: gettext
BuildRequires: gnutls-devel
BuildRequires: openssl-devel
# For ioemu PCI passthrough
BuildRequires: pciutils-devel
# Several tools now use uuid
BuildRequires: libuuid-devel
# modern compressed kernels
BuildRequires: bzip2-devel xz-devel
# libfsimage
BuildRequires: e2fsprogs-devel
# tools now require yajl
BuildRequires: yajl-devel
BuildRequires: git
%if %with_systemd
BuildRequires: pkgconfig(libsystemd-daemon)
%endif
Requires: bridge-utils
Requires: python-lxml
Requires: pciutils
Requires: xen-runtime = %{version}-%{release}
# Not strictly a dependency, but kpartx is by far the most useful tool right
# now for accessing domU data from within a dom0 so bring it in when the user
# installs xen.
Requires: kpartx
Requires: chkconfig
Requires: module-init-tools
Requires: gawk
Requires: grep
#Recommends: xen-ovmf
ExclusiveArch: x86_64 aarch64
%if %with_ocaml
BuildRequires: ocaml ocaml-findlib
%endif
%if %with_spice
BuildRequires: spice-server-devel usbredir-devel
%endif
%if %with_livepatch
BuildRequires: elfutils-libelf-devel
%endif
%ifarch aarch64
BuildRequires: libfdt-devel
%endif

%description
This package contains the xl command line tools, needed to manage
virtual machines running under the Xen hypervisor

%package libs
Summary: Libraries for Xen tools
Group: Development/Libraries
Requires(pre): /sbin/ldconfig
Requires(post): /sbin/ldconfig
Requires: xen-licenses

%description libs
This package contains the libraries needed to run applications
which manage Xen virtual machines.


%package runtime
Summary: Core Xen runtime environment
Group: Development/Libraries
Requires: xen-libs = %{version}-%{release}
%ifarch x86_64
Requires: /usr/bin/qemu-img
Requires: seabios
# xen-ovmf is not being built on CentOS 6 right now.
%if 0%{?centos_ver} > 6
Requires: xen-ovmf
%endif
%endif
# Ensure we at least have a suitable kernel installed, though we can't
# force user to actually boot it.
Requires: xen-hypervisor-abi = %{hv_abi}
# For hotplug scripts (locking.sh)
Requires: perl

%description runtime
This package contains the runtime programs and daemons which
form the core Xen userspace environment.


%package hypervisor
Summary: Libraries for Xen tools
Group: Development/Libraries
Provides: xen-hypervisor-abi = %{hv_abi}
Requires: xen-licenses
Requires: kernel >= 3.4.26

%description hypervisor
This package contains the Xen hypervisor


%package doc
Summary: Xen documentation
Group: Documentation
#BuildArch: noarch
Requires: xen-licenses

%description doc
This package contains the Xen documentation.


%package devel
Summary: Development libraries for Xen tools
Group: Development/Libraries
Requires: xen-libs = %{version}-%{release}

%description devel
This package contains what\'s needed to develop applications
which manage Xen virtual machines.


%package licenses
Summary: License files from Xen source
Group: Documentation

%description licenses
This package contains the license files from the source used
to build the xen packages.


%if %build_ocaml
%package ocaml
Summary: Ocaml libraries for Xen tools
Group: Development/Libraries
Requires: ocaml-runtime, xen-libs = %{version}-%{release}

%description ocaml
This package contains libraries for ocaml tools to manage Xen
virtual machines.


%package ocaml-devel
Summary: Ocaml development libraries for Xen tools
Group: Development/Libraries
Requires: xen-ocaml = %{version}-%{release}

%description ocaml-devel
This package contains libraries for developing ocaml tools to
manage Xen virtual machines.
%endif

%if %with_livepatch
%package livepatch-build-tools
Summary: Tools to build Xen live patches
Group: Development/Libraries
Requires: elfutils
Requires: make
Requires: perl
Requires: sed
Requires: coreutils
Requires: grep
Requires: patch
Requires: gcc

%description livepatch-build-tools
This package contains the tools needed for generating live patches
per https://wiki.xen.org/wiki/LivePatch .
%endif

%prep
%setup -q -n %{xen_tarball_dir}

export XEN_VENDORVERSION="-%{release}"
XEN_VENDORVERSION="${XEN_VENDORVERSION//.centos.alt/}"
export XEN_EXTRAVERSION="%{version}$XEN_VENDORVERSION"
XEN_EXTRAVERSION="${XEN_EXTRAVERSION#%{hv_abi}}"

########################
# To manipulate the am patchqueue (using 4.4.3 as an example):
# 
# * Clone the upstream xen.git repository:
#
# $ git clone git://xenbits.xenproject.org/xen.git xen.git
# $ cd xen.git
#
# * Make a branch based on the target baseline version
#
# $ git checkout -b centos/pq/4.4.3 RELEASE-4.4.3
#
# 2. Import SOURCES/xen-queue.am
# 
# $ git am ${path_to_package_repo}/SOURCES/xen-queue.am
#
# OR using stackgit (recommended):
#
# $ stg init
# $ stg import -M ${path_to_package_repo}/SOURCES/xen-queue.am
#
# (Note the -M -- if you don't specify this, it will only import the
# first patch.)
#
# 3. Manipulate the patchqueue using normal git (or stackgit) commands
#
# 4. Export the queue again:
#
# git format-patch --stdout -N RELEASE-4.4.3 > ${path_to_package_repo}/SOURCES/xen-queue.am
#
########################

# Create a git repo within the expanded tarball.
git init
git config user.email "..."
git config user.name "..."
git config gc.auto 0
# Have to remove the .gitignore so that tools/hotplug/Linux/init.d actually get included in the git tree
rm -f .gitignore
git add .
git commit -a -q -m "%{version}%{?xen_rc} baseline."

# Apply patches to code in the core Xen repo
git am %{PATCH1}

# Prevent the build system from using information of this temporary git tree
rm -rf .git

#Optionally enable live patching
%if %{with_livepatch}
echo "CONFIG_LIVEPATCH=y" > xen/.config
%{__tar} -C ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/ -zxf %{SOURCE60}
%endif

make -C xen olddefconfig

# Now apply patches to things not in the core Xen repo

pushd tools/qemu-xen
# Add qemu-xen (aka "qemu upstream") -related patches here
%ifarch aarch64
%patch2001 -p1
%endif
%patch2002 -p1
popd

pushd tools/qemu-xen-traditional
# Add qemu-traditional-related patches here
popd

%if %{with_blktap}
pushd `pwd`
rm -rf ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/blktap2
%{__tar} -C ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/ -zxf %{SOURCE101}
cd ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/blktap2
./autogen.sh
./configure --libdir=%{_libdir} --prefix=/usr --libexecdir=%{_libexecdir}/xen/bin
popd
# Add blktap-related patches here
%patch1001 -p1
%patch1005 -p1
%patch1006 -p1
%endif

%if %{with_stubdom}
# stubdom sources
cp -v %{SOURCE10} %{SOURCE11} %{SOURCE12} %{SOURCE13} %{SOURCE14} %{SOURCE15} stubdom
%endif

%if %with_tianocore
rm -rf ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/edk2
%{__tar} -C ${RPM_BUILD_DIR}/%{xen_tarball_dir}/tools/ -zxf %{SOURCE53}
%endif


%build
%if !%build_ocaml
%define ocaml_flags OCAML_TOOLS=n
%endif
%if %build_efi
mkdir -p dist/install/boot/efi/efi/%{xen_efi_vendor}
%endif
export XEN_VENDORVERSION="-$(echo %{release} | sed 's/.centos.alt//g')"
export XEN_EXTRAVERSION="%{version}$XEN_VENDORVERSION"
XEN_EXTRAVERSION="${XEN_EXTRAVERSION#%{hv_abi}}"
export XEN_DOMAIN="centos.org"
export debug="n"
# From xen.git/INSTALL
unset CFLAGS CXXFLAGS FFLAGS LDFLAGS
export EXTRA_CFLAGS_XEN_TOOLS="$RPM_OPT_FLAGS"
export EXTRA_CFLAGS_QEMU_TRADITIONAL="$RPM_OPT_FLAGS"
export EXTRA_CFLAGS_QEMU_XEN="$RPM_OPT_FLAGS"
export WGET=$(type -P false)
export GIT=$(type -P false)

%if %{with_blktap}
%define extra_config_blktap --enable-blktap2
%else
%define extra_config_blktap --disable-blktap2
%endif

%if %with_systemd
%define extra_config_systemd --enable-systemd
%else
%define extra_config_systemd --disable-systemd
%endif

%if %with_spice
%define extra_config_spice --with-extra-qemuu-configure-args="--enable-spice --enable-usb-redir"
%endif

%ifarch x86_64
%define extra_config_arch --with-system-seabios=/usr/share/seabios/bios.bin
%define extra_config_ovmf --with-system-ovmf=%{_libexecdir}/xen/boot/OVMF.fd
%endif

%define extra_config %{?extra_config_systemd} %{?extra_config_blktap} %{?extra_config_arch} %{?extra_config_spice} %{?extra_config_ovmf}

WGET=/bin/false ./configure --prefix=/usr --libexecdir=%{_libexecdir} --libdir=%{_libdir} --with-xenstored=xenstored --disable-xsmpolicy %{?extra_config}

export EFI_VENDOR="%{xen_efi_vendor}"
make %{?_smp_mflags} dist-xen
make %{?_smp_mflags} %{?ocaml_flags} dist-tools
make                                 dist-docs

%if %{with_stubdom}
unset EXTRA_CFLAGS_XEN_TOOLS
make %{?ocaml_flags} dist-stubdom
%endif

%if %{with_tianocore}
%ifarch aarch64
pushd `pwd`
cd tools/edk2
make -C BaseTools
export GCC48_AARCH64_PREFIX=
bash -c "source edksetup.sh && build -a AARCH64 -t GCC48 -p ArmVirtPkg/ArmVirtXen.dsc -b RELEASE"
popd
%endif
%endif

%if %{with_livepatch}
pushd `pwd`
cd tools/livepatch-build-tools
make
popd
%endif

%install
rm -rf %{buildroot}
%if %build_ocaml
mkdir -p %{buildroot}%{_libdir}/ocaml/stublibs
%endif
%if %build_efi
mkdir -p %{buildroot}/boot/efi/efi/%{xen_efi_vendor}
%endif
export XEN_VENDORVERSION="-$(echo %{release} | sed 's/.centos.alt//g')"
export XEN_EXTRAVERSION="%{version}$XEN_VENDORVERSION"
XEN_EXTRAVERSION="${XEN_EXTRAVERSION#%{hv_abi}}"
export XEN_DOMAIN="centos.org"
export EFI_VENDOR="%{xen_efi_vendor}"
xen_version="$(make -C xen xenversion --no-print-directory)"
make DESTDIR=%{buildroot} prefix=/usr install-xen
make DESTDIR=%{buildroot} %{?ocaml_flags} prefix=/usr install-tools
make DESTDIR=%{buildroot} prefix=/usr install-docs
%if %{with_stubdom}
make DESTDIR=%{buildroot} %{?ocaml_flags} prefix=/usr install-stubdom
%endif

%if %build_efi
install -m 644 %{SOURCE52} %{buildroot}/boot/efi/efi/%{xen_efi_vendor}/xen-%{version}%{?xen_rc}${XEN_VENDORVERSION}.cfg.sample
mv %{buildroot}/boot/efi/efi %{buildroot}/boot/efi/EFI
%endif

%if %with_tianocore
%ifarch aarch64
install -D -m 644 tools/edk2/Build/ArmVirtXen-AARCH64/RELEASE_GCC48/FV/XEN_EFI.fd %{buildroot}/%{_libexecdir}/xen/boot/XEN_EFI.fd
%endif
%endif

%ifarch x86_64
install -m 644 %{SOURCE50} $RPM_BUILD_ROOT/etc/sysconfig/xen-kernel
%endif

%if %{with_livepatch}
pushd `pwd`
cd tools/livepatch-build-tools
make DESTDIR=%{buildroot} PREFIX=/usr install
popd
%endif

%ifarch aarch64
install -m 644 %{SOURCE51} $RPM_BUILD_ROOT/etc/sysconfig/xen-kernel
%endif

############ debug packaging: list files ############

find %{buildroot} -print | xargs ls -ld | sed -e 's|.*%{buildroot}||' > f1.list

############ kill unwanted stuff ############

# stubdom: newlib
rm -rf %{buildroot}/usr/*-xen-elf

# hypervisor symlinks
rm %{buildroot}/boot/xen-$(sed 's/^\([0-9]\+\.[0-9]\+\)\($\|\.\).*/\1/' <<<"$xen_version").gz
rm %{buildroot}/boot/xen-$(sed 's/^\([0-9]\+\)\..*/\1/' <<<"$xen_version").gz

# silly doc dir fun
rm -fr %{buildroot}%{_datadir}/doc/xen
rm -rf %{buildroot}%{_datadir}/doc/qemu
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_datadir}/doc/%{name}-licenses-%{version}-%{release}

# Pointless helper
rm -f %{buildroot}%{_sbindir}/xen-python-path

# qemu stuff (unused or available from upstream)
rm -rf %{buildroot}/usr/share/xen/man
rm -rf %{buildroot}/usr/bin/qemu-*-xen
rm %{buildroot}/usr/libexec/qemu-bridge-helper
%ifarch x86_64
ln -s qemu-img %{buildroot}/%{_bindir}/qemu-img-xen
ln -s qemu-img %{buildroot}/%{_bindir}/qemu-nbd-xen
%endif
for file in bios.bin openbios-sparc32 openbios-sparc64 ppc_rom.bin \
         pxe-e1000.bin pxe-ne2k_pci.bin pxe-pcnet.bin pxe-rtl8139.bin \
         vgabios.bin vgabios-cirrus.bin video.x openbios-ppc bamboo.dtb
do
	rm -f %{buildroot}/%{_datadir}/xen/qemu/$file
done
rm -f %{buildroot}/%{_mandir}/man1/qemu*
rm -f %{buildroot}/%{_mandir}/man8/qemu*
rm -rf %{buildroot}/%{_prefix}/%{_sysconfdir}

# README's not intended for end users
rm -f %{buildroot}/%{_sysconfdir}/xen/README*

# standard gnu info files
rm -rf %{buildroot}/usr/info

# adhere to Static Library Packaging Guidelines
rm -rf %{buildroot}/%{_libdir}/*.a

%if %build_efi
# clean up extra efi files
rm -rf %{buildroot}/%{_libdir}/efi
%endif


############ fixup files in /etc ############

# modules
%if %with_sysv
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig/modules
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/sysconfig/modules/%{name}.modules
%endif

# logrotate
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
install -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# init scripts
%if %with_systemd
rm %{buildroot}%{_sysconfdir}/rc.d/init.d/xen-watchdog
rm %{buildroot}%{_sysconfdir}/rc.d/init.d/xencommons
rm %{buildroot}%{_sysconfdir}/rc.d/init.d/xendomains
rm %{buildroot}%{_sysconfdir}/rc.d/init.d/xendriverdomain
%endif

# sysconfig
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

# systemd
%if %with_systemd
mkdir -p %{buildroot}/usr/lib/tmpfiles.d
install -m 644 %{SOURCE49} %{buildroot}/usr/lib/tmpfiles.d/xen.conf
%endif

# Not sure why qemu wants to put these here either...
%if %{with_spice}
rm -rf %{buildroot}%{_libdir}/xen/include
rm -rf %{buildroot}%{_libdir}/xen/lib
%endif

# Not sure why qemu makes an x86_64 file when building on aarch64...
%ifarch aarch64
rm -f %{buildroot}%{_sysconfdir}/qemu/target-x86_64.conf
%endif

############ create dirs in /var ############

mkdir -p %{buildroot}%{_localstatedir}/lib/xen/images
mkdir -p %{buildroot}%{_localstatedir}/log/xen/console
mkdir -p %{buildroot}%{_localstatedir}/run/xenstored

############ debug packaging: list files ############

find %{buildroot} -print | xargs ls -ld | sed -e 's|.*%{buildroot}||' > f2.list
diff -u f1.list f2.list || true

############ assemble license files ############

mkdir -p licensedir
# avoid licensedir to avoid recursion, also stubdom/ioemu and dist
# which are copies of files elsewhere
find . -path licensedir -prune -o -path stubdom/ioemu -prune -o \
  -path dist -prune -o -name COPYING -o -name LICENSE | while read file; do
  mkdir -p licensedir/`dirname $file`
  install -m 644 $file licensedir/$file
done

%ifarch x86_64
# Make backwards-compatibility links to /usr/lib/xen/bin
mkdir -p %{buildroot}/usr/lib/xen/bin/
pushd %{buildroot}/usr/lib/xen/bin/
for f in libxl-save-helper xc_save xc_restore pygrub
  do
    ln -sf ../../../lib64/xen/bin/$f .
  done
popd

# ...and /usr/lib/xen/boot
mkdir -p %{buildroot}/usr/lib/xen/boot/
pushd %{buildroot}/usr/lib/xen/boot/
for f in pv-grub-x86_32.gz pv-grub-x86_64.gz ioemu-stubdom.gz xenstore-stubdom.gz xen-shim
  do
    ln -sf ../../../lib64/xen/boot/$f .
  done
popd
%endif
############ all done now ############

%post runtime
%if %with_sysv
/sbin/chkconfig --add xendomains
/sbin/chkconfig --add xencommons
%endif
%if %with_systemd
 /bin/systemctl enable xen-qemu-dom0-disk-backend.service
 /bin/systemctl enable xen-init-dom0.service
 /bin/systemctl enable xenconsoled.service
# /bin/systemctl enable xendomains.service
%endif

%if %with_sysv
if [ $1 != 0 ]; then
  service xencommons restart
fi
%endif

%preun runtime
if [ $1 = 0 ]; then
%if %with_sysv
  /sbin/chkconfig --del xencommons
  /sbin/chkconfig --del xendomains
%endif
%if %with_systemd
 /bin/systemctl disable xen-init-dom0.service
 /bin/systemctl disable xen-qemu-dom0-disk-backend.service
 /bin/systemctl disable xenconsoled.service
# /bin/systemctl disable xendomains.service
%endif
fi

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%post hypervisor
if [ $1 = 1 ] ; then
    if [ -f %{_bindir}/grub-bootxen.sh ]; then
	%{_bindir}/grub-bootxen.sh
    elif [ -f /sbin/grub2-mkconfig -a -f /boot/grub2/grub.cfg ]; then
	/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg
    fi
fi

%postuninstall hypervisor
if [ -f %{_bindir}/grub-bootxen.sh ]; then
    %{_bindir}/grub-bootxen.sh
elif [ -f /sbin/grub2-mkconfig -a -f /boot/grub2/grub.cfg ]; then
    /sbin/grub2-mkconfig -o /boot/grub2/grub.cfg
fi

%clean
rm -rf %{buildroot}

#files -f xen-xm.lang
%files
%defattr(-,root,root)
%doc COPYING README
%{_bindir}/xencons
%{python_sitearch}/%{name}
%{python_sitearch}/xen-*.egg-info

# Startup script
# Guest autostart links
%dir %attr(0700,root,root) %{_sysconfdir}/%{name}/auto
# Autostart of guests
%config(noreplace) %{_sysconfdir}/sysconfig/xendomains

%files libs
%defattr(-,root,root)
%{_libdir}/*.so.*
%{_libdir}/fs

%files runtime
%defattr(-,root,root)
%dir %attr(0700,root,root) %{_sysconfdir}/%{name}
%dir %attr(0700,root,root) %{_sysconfdir}/%{name}/scripts/
%config %attr(0700,root,root) %{_sysconfdir}/%{name}/scripts/*

%if %with_sysv
%{_sysconfdir}/rc.d/init.d/xendomains
%{_sysconfdir}/rc.d/init.d/xendriverdomain
%{_sysconfdir}/rc.d/init.d/xen-watchdog
%{_sysconfdir}/rc.d/init.d/xencommons
%endif
%{_sysconfdir}/bash_completion.d/xl.sh

%if %with_systemd
%{_unitdir}/proc-xen.mount
%{_unitdir}/var-lib-xenstored.mount
%{_unitdir}/xenstored.service
%{_unitdir}/xenconsoled.service
%{_unitdir}/xen-watchdog.service
%{_unitdir}/xen-init-dom0.service
%{_unitdir}/xen-qemu-dom0-disk-backend.service
%{_unitdir}/xendomains.service
%{_unitdir}/xendriverdomain.service
/usr/lib/tmpfiles.d/xen.conf
%endif

%config(noreplace) %{_sysconfdir}/sysconfig/xencommons
%config(noreplace) %{_sysconfdir}/xen/xl.conf
%config(noreplace) %{_sysconfdir}/xen/cpupool
%config(noreplace) %{_sysconfdir}/xen/xlexample*

# Auto-load xen backend drivers
%if %with_sysv
%attr(0755,root,root) %{_sysconfdir}/sysconfig/modules/%{name}.modules
%endif

%if %with_systemd
%config(noreplace) /usr/lib/modules-load.d/xen.conf
%endif

# Rotate console log files
%config(noreplace) %{_sysconfdir}/logrotate.d/xen

# Programs run by other programs
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/bin
%attr(0700,root,root) %{_libdir}/%{name}/bin/*
# QEMU-xen runtime files
%dir %{_datadir}/qemu-xen
%{_datadir}/qemu-xen/*
%{_datadir}/locale/*/LC_MESSAGES/qemu.mo

%ifarch x86_64
# QEMU runtime files
%dir %{_datadir}/%{name}/qemu
%dir %{_datadir}/%{name}/qemu/keymaps
%{_datadir}/%{name}/qemu/keymaps/*
%endif

# man pages
%{_mandir}/man1/xentop.1*
%{_mandir}/man1/xentrace_format.1*
%{_mandir}/man8/xentrace.8*
%{_mandir}/man1/xl.1*
%{_mandir}/man5/xl.cfg.5*
%{_mandir}/man5/xl.conf.5*
%{_mandir}/man5/xlcpupool.cfg.5*
%{_mandir}/man1/xenstore-chmod.1.gz
%{_mandir}/man1/xenstore-ls.1.gz
%{_mandir}/man1/xenstore.1.gz
%{_mandir}/man5/xl-disk-configuration.5.gz
%{_mandir}/man5/xl-network-configuration.5.gz
%{_mandir}/man7/xen-pci-device-reservations.7.gz
%{_mandir}/man7/xen-pv-channel.7.gz
%{_mandir}/man7/xen-tscmode.7.gz
%{_mandir}/man7/xen-vtpm.7.gz
%{_mandir}/man7/xen-vtpmmgr.7.gz
%{_mandir}/man7/xl-numa-placement.7.gz


%{python_sitearch}/fsimage.so
%{python_sitearch}/grub
%{python_sitearch}/pygrub-*.egg-info

# The firmware
# Avoid owning /usr/lib twice on i386
%ifarch x86_64
%if "%{_libdir}" != "/usr/lib"
%dir /usr/lib/%{name}
%dir /usr/lib/%{name}/bin
/usr/lib/%{name}/bin/libxl-save-helper
/usr/lib/%{name}/bin/xc_save
/usr/lib/%{name}/bin/xc_restore
/usr/lib/%{name}/bin/pygrub
%dir /usr/lib/%{name}/boot
/usr/lib/%{name}/boot/pv-grub-x86_32.gz
/usr/lib/%{name}/boot/pv-grub-x86_64.gz
/usr/lib/%{name}/boot/ioemu-stubdom.gz
/usr/lib/%{name}/boot/xenstore-stubdom.gz
/usr/lib/%{name}/boot/xen-shim
%endif
%dir %{_libexecdir}/%{name}/boot
%{_libexecdir}/xen/boot/hvmloader
%{_libexecdir}/xen/boot/ioemu-stubdom.gz
%{_libexecdir}/xen/boot/xenstore-stubdom.gz
%{_libexecdir}/xen/boot/pv-grub-x86_32.gz
%{_libexecdir}/xen/boot/pv-grub-x86_64.gz
%{_libexecdir}/xen/boot/xen-shim
%endif

%if %{with_tianocore}
%ifarch aarch64
%{_libexecdir}/xen/boot/XEN_EFI.fd
%endif
%endif

# General Xen state
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/dump
%dir %{_localstatedir}/lib/%{name}/images
# Xenstore persistent state
%dir %{_localstatedir}/lib/xenstored
# Xenstore runtime state
%dir %attr(0700,root,root) %{_localstatedir}/run/xenstored

# All xenstore CLI tools
%{_bindir}/xenstore
%{_bindir}/xenstore-*
%{_bindir}/pygrub
%{_bindir}/xencov_split
%{_sbindir}/xentrace
%{_sbindir}/xentrace_setmask
%{_sbindir}/xentrace_setsize
%{_bindir}/xentrace_format
%{_sbindir}/flask-*
# Misc stuff
%{_bindir}/xen-cpuid
%{_sbindir}/xen-bugtool
%{_sbindir}/xen-diag
%{_sbindir}/xen-livepatch
%{_sbindir}/xen-tmem-list-parse
%{_sbindir}/xenconsoled
%{_sbindir}/xenlockprof
%{_sbindir}/xenmon.py*
%{_sbindir}/xentop
%{_sbindir}/xenbaked
%{_sbindir}/xenstored
%{_sbindir}/xenpm
%{_sbindir}/xenpmd
%{_sbindir}/xenperf
%{_sbindir}/xenwatchdogd
%{_sbindir}/xl
%{_sbindir}/xen-ringwatch
%{_sbindir}/xencov
#x86-only stuff
%ifarch x86_64
%{_bindir}/qemu-*-xen
%{_bindir}/xen-detect
%{_sbindir}/gdbsx
%{_sbindir}/kdd
%{_sbindir}/td-util
%{_sbindir}/xen-hptool
%{_sbindir}/xen-hvmcrash
%{_sbindir}/xen-hvmctx
%{_sbindir}/xen-lowmemd
%{_sbindir}/xen-mfndump
%{_bindir}/xenalyze
%endif
#blktap
%if %{with_blktap}
%{_sbindir}/tap-ctl
%{_bindir}/vhd-index
%{_bindir}/vhd-update
%{_bindir}/vhd-util
%{_sbindir}/lvm-util
%{_sbindir}/part-util
%{_sbindir}/td-rated
%{_sbindir}/vhdpartx
%endif

# Xen logfiles
%dir %attr(0700,root,root) %{_localstatedir}/log/xen
# Guest/HV console logs
%dir %attr(0700,root,root) %{_localstatedir}/log/xen/console

%files hypervisor
%defattr(-,root,root)
%config(noreplace) /etc/sysconfig/xen-kernel
/boot/xen-%{version}%{?xen_rc:-rc}-%{release}.config
%ifarch x86_64
/boot/xen-%{version}%{?xen_rc:-rc}-%{release}.gz
/boot/xen.gz
%endif
%ifarch aarch64
# fixme, what is this on arch?
#/boot/xen-%{version}-1.el7.centos
/boot/xen-*
/boot/xen
%endif
%if %build_efi
/boot/efi/EFI/%{xen_efi_vendor}/*.efi
/boot/efi/EFI/%{xen_efi_vendor}/*.cfg.sample
%endif

%files doc
%defattr(-,root,root)
%doc docs/misc/
%doc dist/install/usr/share/doc/xen/html

%files devel
%defattr(-,root,root)
%{_includedir}/*.h
%dir %{_includedir}/xen
%{_includedir}/xen/*
%dir %{_includedir}/xenstore-compat
%{_includedir}/xenstore-compat/*

%if %{with_blktap}
%dir %{_includedir}/blktap
%{_includedir}/blktap/*
%dir %{_includedir}/vhd
%{_includedir}/vhd/*
%endif

%{_libdir}/*.so
%ifarch x86_64
%{_libdir}/*.la
%endif

%{_datadir}/pkgconfig/xencall.pc
%{_datadir}/pkgconfig/xencontrol.pc
%{_datadir}/pkgconfig/xendevicemodel.pc
%{_datadir}/pkgconfig/xenevtchn.pc
%{_datadir}/pkgconfig/xenforeignmemory.pc
%{_datadir}/pkgconfig/xengnttab.pc
%{_datadir}/pkgconfig/xenguest.pc
%{_datadir}/pkgconfig/xenlight.pc
%{_datadir}/pkgconfig/xenstat.pc
%{_datadir}/pkgconfig/xenstore.pc
%{_datadir}/pkgconfig/xentoolcore.pc
%{_datadir}/pkgconfig/xentoollog.pc
%{_datadir}/pkgconfig/xenvchan.pc
%{_datadir}/pkgconfig/xlutil.pc

%files licenses
%defattr(-,root,root)
%doc licensedir/*

%if %build_ocaml
%files ocaml
%defattr(-,root,root)
%{_libdir}/ocaml/xen*
%exclude %{_libdir}/ocaml/xen*/*.a
%exclude %{_libdir}/ocaml/xen*/*.cmxa
%exclude %{_libdir}/ocaml/xen*/*.cmx
%{_libdir}/ocaml/stublibs/*.so
%{_libdir}/ocaml/stublibs/*.so.owner
%{_sbindir}/oxenstored
%config(noreplace) %{_sysconfdir}/xen/oxenstored.conf

%files ocaml-devel
%defattr(-,root,root)
%{_libdir}/ocaml/xen*/*.a
%{_libdir}/ocaml/xen*/*.cmxa
%{_libdir}/ocaml/xen*/*.cmx
%endif

%if %with_livepatch
%files livepatch-build-tools
%defattr(-,root,root)
%{_bindir}/livepatch-build
%dir /usr/libexec/livepatch-build-tools
/usr/libexec/livepatch-build-tools/prelink
/usr/libexec/livepatch-build-tools/create-diff-object
/usr/libexec/livepatch-build-tools/livepatch-gcc
%endif

%changelog
* Thu Nov 26 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.102.g17ec9b43af-2
- XSA-355

* Tue Nov 17 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.101.g15b2980972-2
- XSA-351

* Wed Oct 28 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.97.g78d903e95e-2
- XSA 286

* Wed Oct 21 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.88.g1719f79a0e-2
- XSAs 345-347

* Wed Sep 23 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.87.gf58caa40cd-2
- XSAs 336-340,342-344

* Tue Aug 25 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.75.g93be943e7d-2
- XSA-335

* Fri Jul 10 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.75.g93be943e7d-1
- XSAs 317,319,321,327,328

* Mon Jun 15 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.63.gfd6e49ecae-1
- Adding new patch from XSA-320 v2

* Wed Jun 10 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.60.g934d6e1a77-1
- XSA-320

* Tue Apr 14 2020 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.42.g24d62e1262-1
- Update for XSAs 313,314,316,318

* Thu Dec 12 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.36.g6cb1cb9c63-1
- Update to include XSAs 307-311

* Thu Nov 28 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.28.ge4899550ff-1
- Update to include XSA-306

* Wed Nov 13 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4.26.gfde09cb80c-1
- Update to include XSAs 304 and 305

* Fri Nov 01 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4-2
- Update with XSAs 296,298,299,301,302,303

* Thu Jul 04 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.4-1
- Xen 4.10.4 released

* Wed May 15 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.3.38.g48bd9061a2-1
- Update to include XSA 297

* Thu Mar 07 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.3.12.g7842419a6b-1
- Update to include XSAs 284,285,287,288,290-294

* Mon Feb 25 2019 Anthony PERARD <anthony.perard@citrix.com> - 4.10.3-1
- New stable release Xen 4.10.3

* Tue Nov 27 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.2.33.gb6e203bc80-1
- Update to include XSAs 275,279,280

* Thu Nov 15 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.2.27.ge907460fd6-1
- Update to include XSA-282

* Thu Oct 25 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.2.13.g73788eb585-1
- Update to include XSA-278

* Tue Sep 25 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.2-1
- Xen 4.10.2

* Tue Aug 21 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.1.106.g13e85a6dbc-2
- Fix xen version string, in e.g. xl info, so it match the RPM version.
- Also remove the information a xen_changeset, as this information is an
  artefact of the package build.

* Mon Aug 20 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.1.106.g13e85a6dbc-1
- Use a snapshot of the xen git tree instead of a release tarball.
- Have fixes for XSA 268, 269, 272 and 273.

* Mon Jul 30 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.1-2
- Apply XSAs 260-267

In order to apply 263, also backport patches:
- x86: correct ordering of operations during S3 resume
- x86: suppress BTI mitigations around S3 suspend/resume<Paste>
- x86/spec_ctrl: Updates to retpoline-safety decision making

* Wed May 02 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.1-1.el7.centos
- Xen 4.10.1

* Tue Jan 30 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.0-3.el7.centos
- Add missing perl dependency for xen-runtime package

* Mon Jan 29 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.0-2.el7.centos
- Fix xenstored startup issue due to old SElinux policy

* Thu Jan 11 2018 Anthony PERARD <anthony.perard@citrix.com> - 4.10.0-1.el7.centos
- Xen 4.10.0

* Fri Dec 08 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.10.0-0.1.rc8.el7.centos
- Xen 4.10.0-rc8

* Wed Dec 06 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-6.el7.centos
- Apply XSAs 246 and 247

* Fri Nov 24 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-5.el7.centos
- Add OVMF, the guest EFI firmware (available via xen-ovmf package)

* Tue Nov 21 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-4.el7.centos
- Import from upstream the updated optional patch from XSA-240, it is necessary
  to apply the update of XSA-240.
- Import update of XSA-240 (v5)
- Apply the new final patch from XSA-243 (v5)

* Tue Oct 24 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-3.el7.centos
- Apply XSA 236

* Fri Oct 13 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-2.el7.centos
- Import XSAs 237-244

* Wed Sep 13 2017 Anthony PERARD <anthony.perard@citrix.com> - 4.8.2-1.el7.centos
- Update to Xen 4.8.2
- Import XSAs 231-234

* Thu Jun 15 2017 Sarah Newman <srn@prgmr.com> 4.8.1-3.el6.centos
- Import XSAs 216-225
- Update XSAs 218,224 to v3

* Fri Jun 09 2017 Sarah Newman <srn@prgmr.com> 4.8.1-2.el6.centos
- Import XSAs 213-214 (XSA 215 does not apply)
- Enable live patching by default

* Thu Apr 27 2017 Anthony Perard <anthony.perard@citrix.com> 4.8.1-1.el6.centos
- Update to Xen 4.8.1

* Wed Mar 15 2017 Johnny Hughes <johnny@centos.org> 4.6.3-9.el6.centos
- Import XSA 211

* Tue Feb 28 2017 Johnny Hughes <johnny@centos.org> 4.6.3-8.el6.centos
- Import XSA 209

* Wed Feb 15 2017 Johnny Hughes <johnny@centos.org> 4.6.3-7.el6.centos
- Import XSA 207

* Mon Feb 13 2017 Johnny Hughes <johnny@centos.org> 4.6.3-6.el6.centos
- Import XSA 208

* Fri Dec 23 2016 Johnny Hughes <johnny@centos.org> 4.6.3-5.el6.centos
- Import XSAs 199, 200, 201, 202, 204, 204

* Tue Nov 22 2016 George Dunlap <george.dunlap@citrix.com> 4.6.3-4.el6.centos
- Import XSAs 191-193, 195-198.  (Not affected by XSA 194.)

* Mon Oct 03 2016 George Dunlap <george.dunlap@citrix.com> 4.6.3-3.el6.centos
- Import XSA 190

* Wed Sep 07 2016 George Dunlap <george.dunlap@citrix.com> 4.6.3-2.el6.centos
- Import XSAs 185-187
- NB Xen 4.6 isn\'t vulnerable to XSA-188

* Thu Jul 28 2016 George Dunlap <george.dunlap@citrix.com> 4.6.3-1.el6.centos
- Rebase to 4.6.3
- Import XSA-184

* Mon Jul 18 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-13.el6.centos
- Import XSA-175 and XSA-178

* Wed Jul 13 2016 Johnny Hughes <johnny@centos.org> 4.6.1-12.el6.centos
- Import XSA-182 and XSA-183

* Thu May 19 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-11.el6.centos
- Gratuitous release bump due to CBS build failure

* Thu May 19 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-10.el6.centos
- Import XSA-180

* Thu May 19 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-9.el6.centos
- Backport xendomains fixes

* Thu May 12 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-8.el6.centos
- import XSA-176

* Mon May 09 2016 George Dunlap <george.dunlap@citrix.com> 4.6.1-7.el6.centos
- import XSA-179

* Mon Apr 18 2016 Johnny Hughes <johnny@centos.org> 4.6.1-6.el6.centos
- import XSA-173

* Tue Mar 29 2016 George Dunlap <george.dunlap@citrix.com> - 4.6.1-5.el6.centos
- Import XSA-172

* Mon Feb 22 2016 George Dunlap <george.dunlap@citrix.com> - 4.6.1-4.el6.centos
- Add links for stubdom images from /usr/lib into /usr/lib64 for backwards compatibility

* Mon Feb 15 2016 George Dunlap <george.dunlap@citrix.com> - 4.6.1-2.el6.centos
- Add XSAs 154, 170

* Thu Feb 11 2016 George Dunlap <george.dunlap@citrix.com> - 4.6.1-1.el6.centos
- Update to 4.6.1
- Retain two xsa-155 related patches to xen missing from the release
- Retain an xsa-162 related patch to qemu-upstream missing from the release

* Thu Jan 14 2016 George Dunlap <george.dunlap@citrix.com> - 4.6.0-9.el6.centos
- Add XSAs 167-169

* Mon Dec 14 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-8.el6.centos
- Add XSAs 155, 164-166

* Wed Nov 25 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-7.el6.centos
 - Remove XSA-161 (withdrawn)

* Wed Nov 25 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-6.el6.centos
 - Import XSAs 159-163

* Wed Nov 11 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-5.el6.centos
 - Import XSA 156

* Thu Nov 05 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-4.el6.centos
 - Import XSAs 145-153 (including ARM XSAs)

* Thu Nov 05 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-3.el6.centos
 - Rework specfile to make download and contribution easier

* Tue Nov  3 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-2.el6.centos
 - Allow same srpm to build on all platforms (no ifs in Source or Patch sections)

* Mon Oct 19 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0-1.el6.centos
 - Update to 4.6.0 release

* Mon Oct 19 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc4-3.el6.centos
 - Add guest efi bootloader support.  To use set kernel=/usr/lib64/xen/boot/XEN_EFI.fd

* Tue Oct 06 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc4-2.el6.centos
 - Enable spice

* Tue Sep 29 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc4-1.el6.centos
 - Rebase to rc4

* Mon Sep 21 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc3-4.el6.centos
 - Gratuitous bump to re-build with new version of dev86 (0.16.21-5)

* Wed Sep 16 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc3-2.el6.centos
 - Include xen-kernel

* Wed Sep 09 2015 George Dunlap <george.dunlap@citrix.com> - 4.6rc3-1.el6.centos
 - Update to 4.6.0-rc3
 - Upstreamable systemd / selinux fixes

* Wed Sep 09 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0rc2x-4.el6.centos
 - Add aarch64

* Tue Sep 08 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0rc2x-3.el6.centos
 - Switch to systemd for CentOS 7

* Mon Sep 07 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0rc2x-2.el6.centos
 - More 4.6-rc2 fixes

* Tue Sep 01 2015 George Dunlap <george.dunlap@citrix.com> - 4.6.0rc2x-1.el6.centos
 - Update to 4.6.0-rc2 (+change)

* Mon Aug 03 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-8.el6.centos
 - Run grub-bootxen.sh on hypervisor post (un)install

* Thu Jul 30 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-7.el6.centos
 - Import XSA-139
 - Import XSA-140

* Tue Jul 28 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-6.el6.centos
 - Gratuitous revision bump to pull \in new version of seabios

* Tue Jun 30 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-5.el6.centos
 - Import XSA-137
 - Import XSA-138

* Mon Jun  1 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-4.el6.centos
 - Import XSA-134,135,136

* Mon Jun  1 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-3.el6.centos
 - Import XSA-128,129.130,131

* Wed May 13 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-2.el6.centos
 - Import XSA-133

* Thu Apr 23 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.2-1.el6.centos
 - Update to 4.4.2
 - Import XSA-132
* Thu Mar 19 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-10.el6.centos
 - Import XSA-125
 - Import XSA-126
 - Import XSA-127

* Fri Mar 13 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-9.el6.centos
 - Fix issue with blktap that left 'zombie' tapdisk processes around
 - Pass readwrite flag to blktap to make it possible to mount disk images
   from read-only files.

* Thu Mar 12 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-8.el6.centos
 - Import xsa-119

* Thu Mar  5 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-7.el6.centos
 - Import xsa-123

* Thu Mar  5 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-6.el6.centos
 - Import xsa-121, xsa-122

* Wed Jan  7 2015 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-5.el6.centos
 - Import xsa-116

* Mon Dec 15 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-4.el6.centos
 - Disabled xend by default
 - Revert 'choose qdisk first' change

* Thu Dec 11 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-3.el6.centos
 - Backported qdisk persistent grant fix
 - Backported fixes to use tapdisk with HVM guests
 - Backported XSAs 107,109-114
 - Backported fixes to migration, cpupools
 - Remove blktapctl initscripts as it\'s no longer available in 4.4
 - Removed custom xenconsoled and xenstored initscripts in favor of xencommons

* Wed Oct 22 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-2.el6.centos
 - Updated to blktap 2.5 v0.9.2

* Mon Oct 20 2014 Johnny Hughes <johnny@centos.org> - 4.2.5-37.el6.centos
- shifted /etc/sysconfig/xen-kernel to centos-xen-release instead of xen

* Wed Oct 15 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.4.1-1.el6.centos
 - Removed patches which were reflected upstream
 - Took advantage of --with-system-seabios config option to remove seabios patch
 - Included polarssl (now required for pvgrub)

* Wed Oct 15 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.2.5-36.el6.centos
 - Port system over to git patchqueue.

* Thu Oct 9 2014 Johnny Hughes <johnny@centos.org> -  4.2.5-36.el6.centos
- added /etc/sysconfig/xen-kernel for auto grub install options

* Wed Oct 8 2014 George Dunlap <george.dunlap@eu.citrix.com> - 4.2.5-35.el6.centos
 - Remove %{ix86} and ia64 build targets to build with the community build system

* Wed Oct  1 2014 Johnny Hughes <johnny@centos.org> - 4.2.5-34.el6.centos
- Roll in Patch209 (XSA-108, CVE-2014-7188)

* Fri Sep 26 2014 Johnny HUghes <johnny@centos.org> -  4.2.5-33.el6.centos
- upgrade to upstream Xen version 4.2.5
- removed patches that are already part of 4.2.5
- Added Patch205 (XSA-97, CVE-2014-5146,CVE-2014-5149)
- Added Patch206 (XSA-104, CVE-2014-7154)
- Added Patch207 (XSA-105, CVE-2014-7155)
- Added Patch208 (XSA-106, CVE-2014-7156) 

* Mon Jun 16 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-33.el6.centos
- actually apply patch203 :)

* Mon Jun 16 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-32.el6.centos
- Patch203 (XSA-96, CVE-2014-3967 and CVE-2014-3968) added

* Mon May  5 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-31.el6.centos
- Roll in Patch202, XSA-92 (CVE-2014-3124)
- Created Patch201 to allow RHEL7 Beta and RC to boot

* Wed Mar 26 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-30.el6.centos
- roll in Patch200, XSA-89 (CVE-2014-2599)

* Sun Feb 23 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-29.el6.centos
- cleaned up older patches, removed qemu-xen upstream git (Source 100) 
  tarball as it is part of the xen-4.2.4.tar.gz tarball now

* Sat Feb 22 2014 Johnny Hughes <johnny@centos.org> - 4.2.4-28.el6.centos
- upgrade to upstream version 4.2.4

* Tue Feb 11 2014 Johnny Hughes <johnny@centos.org> - 4.2.3-28.el6.centos
- Roll in Patches 153, 154, and 155
  XSA-84 (CVE-2014-1891, CVE-2014-1892, CVE-2014-1893, CVE-2014-1894)
  XSA-85 (CVE-2014-1894), XSA-86 (CVE-2014-1896)

* Fri Jan 24 2014 Johnny Hughes <johnny@centos.org> - 4.2.3-27.el6.centos
- Roll in patches 151 and 152 for the following XSAs:
  XSA-83 (CVE-2104-1642) and XSA-87 (CVE-2014-1666)

* Tue Dec 10 2013 Johnny Hughes <johnny@centos.org> - 4.2.3-26.el6.centos
- Roll in Patches 147, 148, 149, 150 for the following XSAs:
- XSA-74 (CVE-2013-4553), XSA-76 (CVE-2013-4554), XSA-80 (CVE-2013-6400)
- XSA-81 (CVE-2013-6885)

* Sat Nov 23 2013 Johnny Hughes <johnny@centos.org> - 4.2.3-25.el6.centos
- Roll in patch 145 and 146 for XSA-75 (CVE-2013-4551), XSA-78 (CVE-2013-6375) 

* Mon Nov  4 2013 Johnny Hughes <johnny@centos.org> - 4.2.3-24.el6.centos
- Roll in patches 134 to 141, 143 to 144 for the following XSAs:
- XSA-62 (CVE-2013-1442), XSA-63 (CVE-2013-4355), XSA-72 (CVE-2013-4416)
- XSA-64 (CVE-2013-4356), XSA-66 (CVE-2013-4361), XSA-67 (CVE-2013-4368)
- XSA-68 (CVE-2013-4369), XSA-69 (CVE-2013-4370), XSA-70 (CVE-2013-4371)
- XSA-73 (CVE-2013-4494)

* Wed Sep 11 2013 Johnny Hughes <johnny@centos.org> - 4.2.3-23.el6.centos
- upgraded to upstream 4.2.3
- removed patches 66-75, 92-94, 108-132 as they are now rolled into xen-4.2.3 


* Thu Jul 18 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-23.el6.centos
- added Patch131 for XSA-57 (CVE-2013-2211)
- added Patch132 for XSA-58 (CVE-2013-1432)

* Fri Jun 14 2013 Johnny Hughes <johnny@cetnos.org> - 4.2.2-22.el6.centos
- rolled in patches 108 through 130 for XSA-55

* Wed Jun  5 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-21.el6.centos
- remarked out XSA-55 patches while they are being better tested upstream 
- cleaned up XEN_VENDORVERSION to remove .centos.alt

* Wed Jun  5 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-20.el6.centos
- added XEN_VENDORVERSION to the make install section of the spec
- added XEN_DOMAIN=centos.org make and make install sections of the spec

* Tue Jun  4 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-19.el6.centos
- tried to work around an empty XEN_VENDORVERSION in the spec file

* Mon Jun  3 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-18.el6.centos
- added patches 76 to 91 for XSA-55 (No CVE Assigned)
- added patch 92 for XSA-52 (CVE-2013-2076)
- added patch 93 for XSA-53 (CVE-2013-2077)
- added patch 94 for XSA-54 (CVE-2013-2078)
  
* Mon May 27 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-16.el6.centos
- add patch 75 to fix xsa46 regression

* Tue May 21 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-15.el6.centos
- ln sf some files from lib64/xen/bin to lib/xen/bin

* Mon May 20 2013 Johnny Hughes <johnny@centos.org> - 4.2.2-14.el6.centos
- Rolled in patch 74 for XSA-56 (CVE-2013-2072)

* Thu May  2 2013 Johnny Hughes <johnny@centos.org> 4.2.2-12.el6.centos
- Rolled in patches 66 through 73 for XSA-45 (CVE-2013-1918) and XSA-49 (CVE-2013-1952)

* Tue Apr 30 2013 Johnny Hughes <johnny@centos.org> 4.2.2-11.el6.centos
- upgraded to upstream version 4.2.2 for xen
- removed patches 48,57,58,59,61,63,101,102,103,104,108,1002,1004 as
  they are already part of xen-4.2.2
- added patches 64 and 65
- upgraded Source100 to upstream qemu-xen-4.2.2 

* Tue Apr 23 2013 Johnny Hughes <johnny@centos.org> 4.2.1-10.1.el6.centos.9
- Roll in security fix for XSA-48,CVE-2013-1922 (Patch105)
- Roll in patch to add auto option for autoballon(Patch106) and 
  set the autoballon option to auto (Patch107)
- Roll in security fix for XSA-44,CVE-2013-1917 (Patch108) 

* Fri Apr  5 2013 Johnny Hughes <johnny@centos.org> 4.2.1-10.1.el6.centos.8
- added patches 103 and 104.  Patch104 is Security fix for XSA-47,CVE-2013-1920  

* Wed Mar 27 2013 Johnny Hughes <johnny@centos.org> 4.2.1-6.1.el6.centos.8
- build with_ocaml
- roll in xen-centos-blktap25-ctl-ipc-restart.patch 

* Tue Mar 12 2013 Johnny Hughes <johnny@centos.org> 4.2.1-6.1.el6.centos.7
- updated patches for XSA-36 (CVE-2013-0153, Patch101) and XSA-38 (CVE-2013-0215, Patch102).
- rolled in Patch1004 in an effort to fix xl.tapdisk orphaning 

* Tue Feb  5 2013 Johnny Hughes <johnny@centos.org> 4.2.1-6.1.el6.centos.6
- Rolled in patch 101 and 102 to fix CVEs 2013-0153, 2013-0215

* Fri Jan 25 2013 Johnny Hughes <johnny@centos.org> 4.2.1-5.1.el6.centos.6
- added a create for /var/run/xenstored 

* Thu Jan 24 2013 Johnny Hughes <johnny@centos.org> 4.2.1-5.1.el6.centos.5
- Rolled in patches 57, 58, 59, 61, and 62 to incorporate XSA-33, XSA-34, XSA-35, XSA-37, and XSA-41
  to fix CVE's 2012-5634, 2012-6075, 2013-0151, 2013-0152, CVE-2013-0154
- restore status option to xend which is used by libvirt 
 
* Wed Jan 23 2013 Karanbir Singh <kbsingh@centos.org
- Pull in libxl patch to work with blktap25 (from Stefano )
- move blktap25 code into tools/blktap and turn off -Werror (from Stefano )
- Make kernel 3.4.26+ a hard Requires for the xen-hypervisor

* Tue Jan 22 2013 Karanbir Singh <kbsingh@centos.org> - 4.2.1-1.1.el6.centos.4
- add xencommons to chkconfig and set it to start 
- xend needs pciutils 
- import blktap2.5

* Thu Jan 17 2013 Karanbir Singh <kbsingh@centos.org> - 4.2.1-1.1.el6.centos.3
- build with seabious and gpxe
- gpxe does not work, fall back to ipxe
- build with included qemu-xen
- drop in upstream qemu-xen-4.2.1
- upgrade to qemu-upstream-4.2.1

* Fri Jan  4 2013 Johnny Hughes <johnny@centos.org> - 4.2.1-1.1
- set build_efi 0, with_sysv 1,  with_systemd 0  
- remove the BuildRequires that are specific to .f18 dist

* Tue Dec 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-1
- update to xen-4.2.1
- remove patches that are included in 4.2.1
- rebase xen.fedora.efi.build.patch

* Thu Dec 13 2012 Richard W.M. Jones <rjones@redhat.com> - 4.2.0-7
- Rebuild for OCaml fix (RHBZ#877128).

* Mon Dec 03 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-6
- 6 security fixes
  A guest can cause xen to crash [XSA-26, CVE-2012-5510] (#883082)
  An HVM guest can cause xen to run slowly or crash [XSA-27, CVE-2012-5511]
    (#883084)
  A PV guest can cause xen to crash and might be able escalate privileges
    [XSA-29, CVE-2012-5513] (#883088)
  An HVM guest can cause xen to hang [XSA-30, CVE-2012-5514] (#883091)
  A guest can cause xen to hang [XSA-31, CVE-2012-5515] (#883092)
  A PV guest can cause xen to crash and might be able escalate privileges
    [XSA-32, CVE-2012-5525] (#883094)

* Sat Nov 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-5
- two build fixes for Fedora 19
- add texlive-ntgclass package to fix build

* Tue Nov 13 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-4
- 4 security fixes
  A guest can block a cpu by setting a bad VCPU deadline [XSA 20,
    CVE-2012-4535] (#876198)
  HVM guest can exhaust p2m table crashing xen [XSA 22, CVE-2012-4537] (#876203)
  PAE HVM guest can crash hypervisor [XSA-23, CVE-2012-4538] (#876205)
  32-bit PV guest on 64-bit hypervisor can cause an hypervisor infinite
    loop [XSA-24, CVE-2012-4539] (#876207)
- texlive-2012 is now in Fedora 18

* Sun Oct 28 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-3
- texlive-2012 isn't in Fedora 18 yet

* Fri Oct 26 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-2
- limit the size of guest kernels and ramdisks to avoid running out
  of memeory on dom0 during guest boot [XSA-25, CVE-2012-4544] (#870414)

* Thu Oct 25 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-1
- update to xen-4.2.0
- rebase xen-net-disable-iptables-on-bridge.patch pygrubfix.patch
- remove patches that are now upstream or with alternatives upstream
- use ipxe and seabios from seabios-bin and ipxe-roms-qemu packages
- xen tools now need ./configure to be run (x86_64 needs libdir set)
- don't build upstream qemu version
- amend list of files in package - relocate xenpaging
  add /etc/xen/xlexample* oxenstored.conf /usr/include/xenstore-compat/*
      xenstore-stubdom.gz xen-lowmemd xen-ringwatch xl.1.gz xl.cfg.5.gz
      xl.conf.5.gz xlcpupool.cfg.5.gz
- use a tmpfiles.d file to create /run/xen on boot
- add BuildRequires for yajl-devel and graphviz
- build an efi boot image where it is supported
- adjust texlive changes so spec file still works on Fedora 17

* Thu Oct 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-6
- add font packages to build requires due to 2012 version of texlive in F19
- use build requires of texlive-latex instead of tetex-latex which it
  obsoletes

* Wed Oct 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-5
- rebuild for ocaml update

* Thu Sep 06 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-4
- disable qemu monitor by default [XSA-19, CVE-2012-4411] (#855141)

* Wed Sep 05 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-3
- 5 security fixes
  a malicious 64-bit PV guest can crash the dom0 [XSA-12, CVE-2012-3494]
    (#854585)
  a malicious crash might be able to crash the dom0 or escalate privileges
    [XSA-13, CVE-2012-3495] (#854589)
  a malicious PV guest can crash the dom0 [XSA-14, CVE-2012-3496] (#854590)
  a malicious HVM guest can crash the dom0 and might be able to read
    hypervisor or guest memory [XSA-16, CVE-2012-3498] (#854593)
  an HVM guest could use VT100 escape sequences to escalate privileges to
    that of the qemu process [XSA-17, CVE-2012-3515] (#854599)

* Fri Aug 10 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-1 4.1.3-2
- update to 4.1.3
  includes fix for untrusted HVM guest can cause the dom0 to hang or
    crash [XSA-11, CVE-2012-3433] (#843582)
- remove patches that are now upstream
- remove some unnecessary compile fixes
- adjust upstream-23936:cdb34816a40a-rework for backported fix for
    upstream-23940:187d59e32a58
- replace pygrub.size.limits.patch with upstreamed version
- fix for (#845444) broke xend under systemd

* Tue Aug 07 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-25
- remove some unnecessary cache flushing that slow things down
- change python options on xend to reduce selinux problems (#845444)

* Thu Jul 26 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-24
- in rare circumstances an unprivileged user can crash an HVM guest
  [XSA-10,CVE-2012-3432] (#843766)

* Tue Jul 24 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-23
- add a patch to remove a dependency on PyXML and Require python-lxml
  instead of PyXML (#842843)

* Sun Jul 22 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-22
- adjust systemd service files not to report failures when running without
  a hypervisor or when xendomains.service doesn't find anything to start

* Sun Jul 22 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.1.2-21
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-20
- Apply three security patches
  64-bit PV guest privilege escalation vulnerability [CVE-2012-0217]
  guest denial of service on syscall/sysenter exception generation
    [CVE-2012-0218]
  PV guest host Denial of Service [CVE-2012-2934]

* Sat Jun 09 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-19
- adjust xend.service systemd file to avoid selinux problems

* Fri Jun 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-18
- Enable xenconsoled by default under systemd (#829732)

* Thu May 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-16 4.1.2-17
- make pygrub cope better with big files from guest (#818412 CVE-2012-2625)
- add patch from 4.1.3-rc2-pre to build on F17/8

* Sun Apr 15 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-15
- Make the udev tap rule more specific as it breaks openvpn (#812421)
- don't try setuid in xend if we don't need to so selinux is happier

* Sat Mar 31 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-14
- /var/lib/xenstored mount has wrong selinux permissions in latest Fedora
- load xen-acpi-processor module (kernel 3.4 onwards) if present

* Thu Mar 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-13
- fix a packaging error

* Thu Mar 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-12
- fix an error in an rpm script from the sysv configuration removal
- migrate xendomains script to systemd

* Wed Feb 29 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-11
- put the systemd files back in the right place

* Wed Feb 29 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-10
- clean up systemd and sysv configuration including removal of migrated
  sysv files for fc17+

* Sat Feb 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-9
- move xen-watchdog to systemd

* Wed Feb 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-8
- relocate systemd files for fc17+

* Tue Feb 07 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-7
- move xend and xenconsoled to systemd

* Thu Feb 02 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-6
- Fix buffer overflow in e1000 emulation for HVM guests [CVE-2012-0029]

* Sat Jan 28 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-5
- Start building xen's ocaml libraries if appropriate unless --without ocaml
  was specified
- add some backported patches from xen unstable (via Debian) for some
  ocaml tidying and fixes

* Sun Jan 15 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-4
- actually apply the xend-pci-loop.patch
- compile fixes for gcc-4.7

* Wed Jan 11 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-3
- Add xend-pci-loop.patch to stop xend crashing with weird PCI cards (#767742)
- avoid a backtrace if xend can't log to the standard file or a 
  temporary directory (part of #741042)

* Mon Nov 21 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-2
- Fix lost interrupts on emulated devices
- stop xend crashing if its state files are empty at start up
- avoid a python backtrace if xend is run on bare metal
- update grub2 configuration after the old hypervisor has gone
- move blktapctrl to systemd
- Drop obsolete dom0-kernel.repo file

* Fri Oct 21 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-1
- update to 4.1.2
  remove upstream patches xen-4.1-testing.23104 and xen-4.1-testing.23112

* Fri Oct 14 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-8
- more pygrub improvements for grub2 on guest

* Thu Oct 13 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-7
- make pygrub work better with GPT partitions and grub2 on guest

* Thu Sep 29 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-5 4.1.1-6
- improve systemd functionality

* Wed Sep 28 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-4
- lsb header fixes - xenconsoled shutdown needs xenstored to be running
- partial migration to systemd to fix shutdown delays
- update grub2 configuration after hypervisor updates

* Sun Aug 14 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-3
- untrusted guest controlling PCI[E] device can lock up host CPU [CVE-2011-3131]

* Wed Jul 20 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-2
- clean up patch to solve a problem with hvmloader compiled with gcc 4.6

* Wed Jun 15 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-1
- update to 4.1.1
  includes various bugfixes and fix for [CVE-2011-1898] guest with pci
  passthrough can gain privileged access to base domain
- remove upstream cve-2011-1583-4.1.patch 

* Mon May 09 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-2
- Overflows in kernel decompression can allow root on xen PV guest to gain
  privileged access to base domain, or access to xen configuration info.
  Lack of error checking could allow DoS attack from guest [CVE-2011-1583]
- Don't require /usr/bin/qemu-nbd as it isn't used at present.

* Fri Mar 25 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-1
- update to 4.1.0 final

* Tue Mar 22 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-0.1.rc8
- update to 4.1.0-rc8 release candidate
- create xen-4.1.0-rc8.tar.xz file from git/hg repositories
- rebase xen-initscript.patch xen-dumpdir.patch
  xen-net-disable-iptables-on-bridge.patch localgcc45fix.patch
  sysconfig.xenstored init.xenstored
- remove unnecessary or conflicting xen-xenstore-cli.patch localpy27fixes.patch
  xen.irq.fixes.patch xen.xsave.disable.patch xen.8259afix.patch
  localcleanups.patch libpermfixes.patch
- add patch to allow pygrub to work with single partitions with boot sectors
- create ipxe-git-v1.0.0.tar.gz from http://git.ipxe.org/ipxe.git
  to avoid downloading at build time
- no need to move udev rules or init scripts as now created in the right place
- amend list of files shipped - remove fs-backend
  add init.d scripts xen-watchdog xencommons
  add config files xencommons xl.conf cpupool
  add programs kdd tap-ctl xen-hptool xen-hvmcrash xenwatchdogd

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0.1-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jan 31 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-9
- Make libraries executable so that rpm gets dependencies right

* Sat Jan 29 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-8
- Temporarily turn off some compile options so it will build on rawhide

* Fri Jan 28 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-7
- ghost directories in /var/run (#656724)
- minor fixes to /usr/share/doc/xen-doc-4.?.?/misc/network_setup.txt (#653159)
  /etc/xen/scripts/network-route, /etc/xen/scripts/vif-common.sh (#669747)
  and /etc/sysconfig/modules/xen.modules (#656536)

* Tue Oct 12 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-6
- add upstream xen patch xen.8259afix.patch to fix boot panic
  "IO-APIC + timer doesn't work!" (#642108)

* Thu Oct 07 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-5
- add ext4 support for pvgrub (grub-ext4-support.patch from grub-0.97-66.fc14)

* Wed Sep 29 2010 jkeating - 4.0.1-4
- Rebuilt for gcc bug 634757

* Fri Sep 24 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-3
- create symlink for qemu-dm on x86_64 for compatibility with 3.4
- apply some patches destined for 4.0.2
    add some irq fixes
    disable xsave which causes problems for HVM

* Sun Aug 29 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-2
- fix compile problems on Fedora 15, I suspect due to gcc 4.5.1

* Wed Aug 25 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-1
- update to 4.0.1 release - many bug fixes
- xen-dev-create-cleanup.patch no longer needed
- remove part of localgcc45fix.patch no longer needed
- package new files /etc/bash_completion.d/xl.sh
  and /usr/sbin/gdbsx
- add patch to get xm and xend working with python 2.7

* Mon Aug 2 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-5
- add newer module names and xen-gntdev to xen.modules
- Update dom0-kernel.repo file to use repos.fedorapeople.org location

* Mon Jul 26 2010 Michael Young <m.a.young@durham.ac.uk>
- create a xen-licenses package to satisfy revised the Fedora
  Licensing Guidelines

* Sun Jul 25 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-4
- fix gcc 4.5 compile problems

* Thu Jul 22 2010 David Malcolm <dmalcolm@redhat.com> - 4.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Sun Jun 20 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-2
- add patch to remove some old device creation code that doesn't
  work with the latest pvops kernels

* Mon Jun 7 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-1
- update to 4.0.0 release
- rebase xen-initscript.patch and xen-dumpdir.patch patches
- adjust spec file for files added to or removed from the packages
- add new build dependencies libuuid-devel and iasl

* Tue Jun 1 2010 Michael Young <m.a.young@durham.ac.uk> - 3.4.3-1
- update to 3.4.3 release including
    support for latest pv_ops kernels (possibly incomplete)
    should fix build problems (#565063) and crashes (#545307)
- replace Prereq: with Requires: in spec file
- drop static libraries (#556101)

* Thu Dec 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.2-2
- adapt module load script to evtchn.ko -> xen-evtchn.ko rename.

* Thu Dec 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.2-1
- update to 3.4.2 release.
- drop backport patches.

* Thu Oct 8 2009 Justin M. Forbes <jforbes@redhat.com> - 3.4.1-5
- add PyXML to dependencies. (#496135)
- Take ownership of {_libdir}/fs (#521806)

* Mon Sep 14 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-4
- add e2fsprogs-devel to build dependencies.

* Wed Sep 2 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-3
- swap bzip2+xz linux kernel compression support patches.
- backport one more bugfix (videoram option).

* Tue Sep 1 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-2
- backport bzip2+xz linux kernel compression support.
- backport a few bugfixes.

* Fri Aug 7 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-1
- update to 3.4.1 release.

* Wed Aug 5 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-4
- Kill info files.  No xen docs, just standard gnu stuff.
- kill -Werror in tools/libxc to fix build.

* Mon Jul 27 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu May 28 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-2
- rename info files to fix conflict with binutils.
- add install-info calls for the doc subpackage.
- un-parallelize doc build.

* Wed May 27 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-1
- update to version 3.4.0.
- cleanup specfile, add doc subpackage.

* Tue Mar 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-11
- fix python 2.6 warnings.

* Fri Mar 6 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-9
- fix xen.modules init script for pv_ops kernel.
- stick rpm release tag into XEN_VENDORVERSION.
- use %{ix86} macro in ExclusiveArch.
- keep blktapctrl turned off by default.

* Mon Mar 2 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-7
- fix xenstored init script for pv_ops kernel.

* Fri Feb 27 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-6
- fix xenstored crash.
- backport qemu-unplug patch.

* Tue Feb 24 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-5
- fix gcc44 build (broken constrain in inline asm).
- fix ExclusiveArch

* Tue Feb 3 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-3
- backport bzImage support for dom0 builder.

* Sun Jan 18 2009 Tomas Mraz <tmraz@redhat.com> - 3.3.1-2
- rebuild with new openssl

* Thu Jan 8 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-1
- update to xen 3.3.1 release.

* Wed Dec 17 2008 Gerd Hoffmann <kraxel@redhat.com> - 3.3.0-2
- build and package stub domains (pvgrub, ioemu).
- backport unstable fixes for pv_ops dom0.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 3.3.0-1.1
- Rebuild for Python 2.6

* Fri Aug 29 2008 Daniel P. Berrange <berrange@redhat.com> - 3.3.0-1.fc10
- Update to xen 3.3.0 release

* Wed Jul 23 2008 Mark McLoughlin <markmc@redhat.com> - 3.2.0-17.fc10
- Enable xen-hypervisor build
- Backport support for booting DomU from bzImage
- Re-diff all patches for zero fuzz

* Wed Jul  9 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-16.fc10
- Remove bogus ia64 hypercall arg (rhbz #433921)

* Fri Jun 27 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-15.fc10
- Re-enable QEMU image format auto-detection, without the security
  loopholes

* Wed Jun 25 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-14.fc10
- Rebuild for GNU TLS ABI change

* Fri Jun 13 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-13.fc10
- Correctly limit PVFB size (CVE-2008-1952)

* Tue Jun  3 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-12.fc10
- Move /var/run/xend into xen-runtime for pygrub (rhbz #442052)

* Wed May 14 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-11.fc10
- Disable QEMU image format auto-detection (CVE-2008-2004)
- Fix PVFB to validate frame buffer description (CVE-2008-1943)

* Wed Feb 27 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-10.fc9
- Fix block device checks for extendable disk formats

* Wed Feb 27 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-9.fc9
- Let XenD setup QEMU logfile (rhbz #435164)
- Fix PVFB use of event channel filehandle

* Sat Feb 23 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-8.fc9
- Fix block device extents check (rhbz #433560)

* Mon Feb 18 2008 Mark McLoughlin <markmc@redhat.com> - 3.2.0-7.fc9
- Restore some network-bridge patches lost during 3.2.0 rebase

* Wed Feb  6 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-6.fc9
- Fixed xenstore-ls to automatically use xenstored socket as needed

* Sun Feb  3 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-5.fc9
- Fix timer mode parameter handling for HVM
- Temporarily disable all Latex docs due to texlive problems (rhbz #431327)

* Fri Feb  1 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-4.fc9
- Add a xen-runtime subpackage to allow use of Xen without XenD
- Split init script out to one script per daemon
- Remove unused / broken / obsolete tools

* Mon Jan 21 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-3.fc9
- Remove legacy dependancy on python-virtinst

* Mon Jan 21 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-2.fc9
- Added XSM header files to -devel RPM

* Fri Jan 18 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-1.fc9
- Updated to 3.2.0 final release

* Thu Jan 10 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-0.fc9.rc5.dev16701.1
- Rebase to Xen 3.2 rc5 changeset 16701

* Thu Dec 13 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.2-3.fc9
- Re-factor to make it easier to test dev trees in RPMs
- Include hypervisor build if doing a dev RPM

* Fri Dec 07 2007 Release Engineering <rel-eng@fedoraproject.org> - 3.1.2-2.fc9
- Rebuild for deps

* Sat Dec  1 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.2-1.fc9
- Upgrade to 3.1.2 bugfix release

* Sat Nov  3 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-14.fc9
- Disable network-bridge script since it conflicts with NetworkManager
  which is now on by default

* Fri Oct 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-13.fc9
- Fixed xenbaked tmpfile flaw (CVE-2007-3919)

* Wed Oct 10 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-12.fc8
- Pull in QEMU BIOS boot menu patch from KVM package
- Fix QEMU patch for locating x509 certificates based on command line args
- Add XenD config options for TLS x509 certificate setup

* Wed Sep 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-11.fc8
- Fixed rtl8139 checksum calculation for Vista (rhbz #308201)

* Wed Sep 26 2007 Chris Lalancette <clalance@redhat.com> - 3.1.0-10.fc8
- QEmu NE2000 overflow check - CVE-2007-1321
- Pygrub guest escape - CVE-2007-4993

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-9.fc8
- Fix generation of manual pages (rhbz #250791)
- Really fix FC-6 32-on-64 guests

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-8.fc8
- Make 32-bit FC-6 guest PVFB work on x86_64 host

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-7.fc8
- Re-add support for back-compat FC6 PVFB support
- Fix handling of explicit port numbers (rhbz #279581)

* Wed Sep 19 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-6.fc8
- Don't clobber the VIF type attribute in FV guests (rhbz #296061)

* Tue Aug 28 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-5.fc8
- Added dep on openssl for blktap-qcow

* Tue Aug 28 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-4.fc8
- Switch PVFB over to use QEMU
- Backport QEMU VNC security patches for TLS/x509

* Wed Aug  1 2007 Markus Armbruster <armbru@redhat.com> - 3.1.0-3.fc8
- Put guest's native protocol ABI into xenstore, to provide for older
  kernels running 32-on-64.
- VNC keymap fixes
- Fix race conditions in LibVNCServer on client disconnect

* Tue Jun 12 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-2.fc8
- Remove patch which kills VNC monitor
- Fix HVM save/restore file path to be /var/lib/xen instead of /tmp
- Don't spawn a bogus xen-vncfb daemon for HVM guests
- Add persistent logging of hypervisor & guest consoles
- Add /etc/sysconfig/xen to allow admin choice of logging options
- Re-write Xen startup to use standard init script functions
- Add logrotate configuration for all xen related logs

* Fri May 25 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-1.fc8
- Updated to official 3.1.0 tar.gz
- Fixed data corruption from VNC client disconnect (bz 241303)

* Thu May 17 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-0.rc7.2.fc7
- Ensure xen-vncfb processes are cleanedup if guest quits (bz 240406)
- Tear down guest if device hotplug fails

* Thu May  3 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-0.rc7.1.fc7
- Updated to 3.1.0 rc7, changeset  15021 (upstream renumbered from 3.0.5)

* Tue May  1 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.4.fc7
- Fix op_save RPC API

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.3.fc7
- Added BR on gettext

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.2.fc7
- Redo failed build.

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.1.fc7
- Updated to 3.0.5 rc4, changeset 14993
- Reduce number of xenstore transactions used for listing domains
- Hack to pre-balloon 2 MB for PV guests as well as HVM

* Thu Apr 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc3.14934.2.fc7
- Fixed display of bootloader menu with xm create -c
- Added modprobe for both xenblktap & blktap to deal with rename issues
- Hack to pre-balloon 10 MB for HVM guests

* Thu Apr 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc3.14934.1.fc7
- Updated to 3.0.5 rc3, changeset 14934
- Fixed networking for service xend restart & minor IPv6 tweak

* Tue Apr 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc2.14889.2.fc7
- Fixed vfb/vkbd device startup race

* Tue Apr 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc2.14889.1.fc7
- Updated to xen 3.0.5 rc2, changeset 14889
- Remove use of netloop from network-bridge script
- Add backcompat support to vif-bridge script to translate xenbrN to ethN

* Wed Mar 14 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-9.fc7
- Disable access to QEMU monitor over VNC (CVE-2007-0998, bz 230295)

* Tue Mar  6 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-8.fc7
- Close QEMU file handles when running network script

* Fri Mar  2 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-7.fc7
- Fix interaction of bootloader with blktap (bz 230702)
- Ensure PVFB daemon terminates if domain doesn't startup (bz 230634)

* Thu Feb  8 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-6.fc7
- Setup readonly loop devices for readonly disks
- Extended error reporting for hotplug scripts
- Pass all 8 mouse buttons from VNC through to kernel

* Tue Jan 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-5.fc7
- Don't run the pvfb daemons for HVM guests (bz 225413)
- Fix handling of vnclisten parameter for HVM guests

* Tue Jan 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-4.fc7
- Fix pygrub memory corruption

* Tue Jan 23 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-3.fc7
- Added PVFB back compat for FC5/6 guests

* Mon Jan 22 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-2.fc7
- Ensure the arch-x86 header files are included in xen-devel package
- Bring back patch to move /var/xen/dump to /var/lib/xen/dump
- Make /var/log/xen mode 0700

* Thu Jan 11 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-1
- Upgrade to official xen-3.0.4_1 release tarball

* Thu Dec 14 2006 Jeremy Katz <katzj@redhat.com> - 3.0.3-3
- fix the build

* Thu Dec  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0.3-2
- rebuild for python 2.5

* Tue Oct 24 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.3-1
- Pull in the official 3.0.3 tarball of xen (changeset 11774).
- Add patches for VNC password authentication (bz 203196)
- Switch /etc/xen directory to be mode 0700 because the config files
  can contain plain text passwords (bz 203196)
- Change the package dependency to python-virtinst to reflect the
  package name change.
- Fix str-2-int cast of VNC port for paravirt framebuffer (bz 211193)

* Wed Oct  4 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-44
- fix having "many" kernels in pygrub

* Wed Oct  4 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-43
- Fix SMBIOS tables for SVM guests [danpb] (bug 207501)

* Fri Sep 29 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.2-42
- Added vnclisten patches to make VNC only listen on localhost
  out of the box, configurable by 'vnclisten' parameter (bz 203196)

* Thu Sep 28 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-41
- Update to xen-3.0.3-testing changeset 11633

* Thu Sep 28 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-40
- Workaround blktap/xenstore startup race
- Add udev rules for xen blktap devices (srostedt)
- Add support for dynamic blktap device nodes (srostedt)
- Fixes for infinite dom0 cpu usage with blktap
- Fix xm not to die on malformed "tap:" blkif config string
- Enable blktap on kernels without epoll-for-aio support.
- Load the blktap module automatically at startup
- Reenable blktapctrl

* Wed Sep 27 2006 Daniel Berrange <berrange@redhat.com> - 3.0.2-39
- Disable paravirt framebuffer server side rendered cursor (bz 206313)
- Ignore SIGPIPE in paravirt framebuffer daemon to avoid terminating
  on client disconnects while writing data (bz 208025)

* Wed Sep 27 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-38
- Fix cursor in pygrub (#208041)

* Tue Sep 26 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.2-37
- Removed obsolete scary warnings in package description

* Thu Sep 21 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-36
- Add Requires: kpartx for dom0 access to domU data

* Wed Sep 20 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-35
- Don't strip qemu-dm early, so that we get proper debuginfo (danpb)
- Fix compile problem with latest glibc

* Wed Sep 20 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-34
- Update to xen-unstable changeset 11539
- Threading fixes for libVNCserver (danpb)

* Tue Sep  5 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-33
- update pvfb patch based on upstream feedback

* Tue Sep  5 2006 Juan Quintela <quintela@redhat.com> - 3.0.2-31
- re-enable ia64.

* Thu Aug 31 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-31
- update to changeset 11405

* Thu Aug 31 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-30
- fix pvfb for x86_64

* Wed Aug 30 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-29
- update libvncserver to hopefully fix problems with vnc clients disconnecting

* Tue Aug 29 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-28
- fix a typo

* Mon Aug 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-27
- add support for paravirt framebuffer

* Mon Aug 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-26
- update to xen-unstable cs 11251
- clean up patches some
- disable ia64 as it doesn't currently build 

* Tue Aug 22 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-25
- make initscript not spew on non-xen kernels (#202945)

* Mon Aug 21 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-24
- remove copy of xenguest-install from this package, require 
  python-xeninst (the new home of xenguest-install)

* Wed Aug  2 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-23
- add patch to fix rtl8139 in FV, switch it back to the default nic
- add necessary ia64 patches (#201040)
- build on ia64

* Fri Jul 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-22
- add patch to fix net devices for HVM guests 

* Fri Jul 28 2006 Rik van Riel <riel@redhat.com> - 3.0.2-21
- make sure disk IO from HVM guests actually hits disk (#198851)

* Fri Jul 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-20
- don't start blktapctrl for now
- fix HVM guest creation in xenguest-install
- make sure log files have the right SELinux label

* Tue Jul 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-19
- fix libblktap symlinks (#199820)
- make libxenstore executable (#197316)
- version libxenstore (markmc) 

* Fri Jul 21 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-18
- include /var/xen/dump in file list
- load blkbk, netbk and netloop when xend starts
- update to cs 10712
- avoid file conflicts with qemu (#199759)

* Wed Jul 19 2006 Mark McLoughlin <markmc@redhat.com> - 3.0.2-17
- libxenstore is unversioned, so make xen-libs own it rather
  than xen-devel

* Wed Jul 19 2006 Mark McLoughlin <markmc@redhat.com> 3.0.2-16
- Fix network-bridge error (#199414)

* Mon Jul 17 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-15
- desactivating the relocation server in xend conf by default and
  add a warning text about it.

* Thu Jul 13 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-14
- Compile fix: don't #include <linux/compiler.h>

* Thu Jul 13 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-13
- Update to xen-unstable cset 10675
- Remove internal libvncserver build, new qemu device model has its own one
  now.
- Change default FV NIC model from rtl8139 to ne2k_pci until the former works
  better

* Tue Jul 11 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-12
- bump libvirt requires to 0.1.2
- drop xend httpd localhost server and use the unix socket instead

* Mon Jul 10 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-11
- split into main packages + -libs and -devel subpackages for #198260
- add patch from jfautley to allow specifying other bridge for 
  xenguest-install (#198097)

* Mon Jul  3 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-10
- make xenguest-install work with relative paths to disk 
  images (markmc, #197518)

* Fri Jun 23 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-9
- own /var/run/xend for selinux (#196456, #195952)

* Tue Jun 13 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-8
- fix syntax error in xenguest-install

* Mon Jun 12 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-7
- more initscript patch to report status #184452

* Wed Jun  7 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-6
- Add BuildRequires: for gnu/stubs-32.h so that x86_64 builds pick up
  glibc32 correctly

* Wed Jun  7 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-5
- Rebase to xen-unstable cset 10278

* Fri May  5 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-4
- update to new snapshot (changeset 9925)

* Thu Apr 27 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-3
- xen.h now requires xen-compat.h, install it too

* Wed Apr 26 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-2
- -m64 patch isn't needed anymore either

* Tue Apr 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-1
- update to post 3.0.2 snapshot (changeset:   9744:1ad06bd6832d)
- stop applying patches that are upstreamed
- add patches for bootloader to run on all domain creations
- make xenguest-install create a persistent uuid
- use libvirt for domain creation in xenguest-install, slightly improve 
  error handling

* Tue Apr 18 2006 Daniel Veillard <veillard@redhat.com> - 3.0.1-5
- augment the close on exec patch with the fix for #188361

* Thu Mar  9 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-4
- add udev rule so that /dev/xen/evtchn gets created properly
- make pygrub not use /tmp for SELinux
- make xenguest-install actually unmount its nfs share.  also, don't use /tmp

* Tue Mar  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-3
- set /proc/xen/privcmd and /var/log/xend-debug.log as close on exec to avoid
  SELinux problems
- give better feedback on invalid urls (#184176)

* Mon Mar  6 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-2
- Use kva mmap to find the xenstore page (upstream xen-unstable cset 9130)

* Mon Mar  6 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-1
- fix xenguest-install so that it uses phy: for block devices instead of 
  forcing them over loopback.  
- change package versioning to be a little more accurate

* Thu Mar  2 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060301.fc5.3
- Remove unneeded CFLAGS spec file hack

* Thu Mar  2 2006 Rik van Riel <riel@redhat.com> - 3.0.1-0.20060301.fc5.2
- fix 64 bit CFLAGS issue with vmxloader and hvmloader

* Wed Mar  1 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060301.fc5.1
- Update to xen-unstable cset 9022

* Tue Feb 28 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060228.fc5.1
- Update to xen-unstable cset 9015

* Thu Feb 23 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.3
- add patch to ensure we get a unique fifo for boot loader (#182328)
- don't try to read the whole disk if we can't find a partition table 
  with pygrub 
- fix restarting of domains (#179677)

* Thu Feb  9 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.2
- fix -h conflict for xenguest-isntall

* Wed Feb  8 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.1
- turn on http listener so you can do things with libvir as a user

* Wed Feb  8 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5
- update to current hg snapshot for HVM support
- update xenguest-install for hvm changes.  allow hvm on svm hardware
- fix a few little xenguest-install bugs

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.6
- add a hack to fix VMX guests with video to balloon enough (#180375)

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.5
- fix build for new udev

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.4
- patch from David Lutterkort to pass macaddr (-m) to xenguest-install
- rework xenguest-install a bit so that it can be used for creating 
  fully-virtualized guests as well as paravirt.  Run with --help for 
  more details (or follow the prompts)
- add more docs (noticed by Andrew Puch)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 3.0-0.20060130.fc5.3.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Feb  2 2006 Bill Nottingham <notting@redhat.com> 3.0-0.20060130.fc5.3
- disable iptables/ip6tables/arptables on bridging when bringing up a
  Xen bridge. If complicated filtering is needed that uses this, custom
  firewalls will be needed. (#177794)

* Tue Jan 31 2006 Bill Nottingham <notting@redhat.com> 3.0-0.20060130.fc5.2
- use the default network device, don't hardcode eth0

* Tue Jan 31 2006  <sct@redhat.com> - 3.0-0.20060130.fc5.1
- Add xenguest-install.py in /usr/sbin

* Mon Jan 30 2006  <sct@redhat.com> - 3.0-0.20060130.fc5
- Update to xen-unstable from 20060130 (cset 8705)

* Wed Jan 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060110.fc5.5
- buildrequire dev86 so that vmx firmware gets built
- include a copy of libvncserver and build vmx device models against it 

* Tue Jan 24 2006 Bill Nottingham <notting@redhat.com> - 3.0-0.20060110.fc5.4
- only put the udev rules in one place

* Fri Jan 20 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060110.fc5.3
- move xsls to xenstore-ls to not conflict (#171863)

* Tue Jan 10 2006  <sct@redhat.com> - 3.0-0.20060110.fc5.1
- Update to xen-unstable from 20060110 (cset 8526)

* Thu Dec 22 2005 Jesse Keating <jkeating@redhat.com> - 3.0-0.20051206.fc5.2
- rebuilt

* Tue Dec  6 2005 Juan Quintela <quintela@trasno.org> - 3.0-0.20051206.fc5.1
- 20051206 version (should be 3.0.0).
- Remove xen-bootloader fixes (integrated upstream).

* Wed Nov 30 2005 Daniel Veillard <veillard@redhat.com> - 3.0-0.20051109.fc5.4
- adding missing headers for libxenctrl and libxenstore
- use libX11-devel build require instead of xorg-x11-devel

* Mon Nov 14 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.3
- change default dom0 min-mem to 256M so that dom0 will try to balloon down

* Sat Nov 12 2005 Jeremy Katz <katzj@redhat.com>
- buildrequire ncurses-devel (reported by Justin Dearing)

* Thu Nov 10 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.2
- actually enable the initscripts

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.1
- udev rules moved

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5
- update to current -unstable
- add patches to fix pygrub 

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051108.fc5
- update to current -unstable

* Fri Oct 21 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051021.fc5
- update to current -unstable

* Thu Sep 15 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20050912.fc5.1
- doesn't require twisted anymore

* Mon Sep 12 2005 Rik van Riel <riel@redhat.com> 3.0-0.20050912.fc5
- add /var/{lib,run}/xenstored to the %files section (#167496, #167121)
- upgrade to today's Xen snapshot
- some small build fixes for x86_64
- enable x86_64 builds

* Thu Sep  8 2005 Rik van Riel <riel@redhat.com> 3.0-0.20050908
- explicitly call /usr/sbin/xend from initscript (#167407)
- add xenstored directories to spec file (#167496, #167121)
- misc gcc4 fixes 
- spec file cleanups (#161191)
- upgrade to today's Xen snapshot
- change the version to 3.0-0.<date> (real 3.0 release will be 3.0-1)

* Tue Aug 23 2005 Rik van Riel <riel@redhat.com> 2-20050823
- upgrade to today's Xen snapshot

* Mon Aug 15 2005 Rik van Riel <riel@redhat.com> 2-20050726
- upgrade to a known-working newer Xen, now that execshield works again

* Mon May 30 2005 Rik van Riel <riel@redhat.com> 2-20050530
- create /var/lib/xen/xen-db/migrate directory so "xm save" works (#158895)

* Mon May 23 2005 Rik van Riel <riel@redhat.com> 2-20050522
- change default display method for VMX domains to SDL

* Fri May 20 2005 Rik van Riel <riel@redhat.com> 2-20050520
- qemu device model for VMX

* Thu May 19 2005 Rik van Riel <riel@redhat.com> 2-20050519
- apply some VMX related bugfixes

* Mon Apr 25 2005 Rik van Riel <riel@redhat.com> 2-20050424
- upgrade to last night's snapshot

* Fri Apr 15 2005 Jeremy Katz <katzj@redhat.com>
- patch manpath instead of moving in specfile.  patch sent upstream
- install to native python path instead of /usr/lib/python
- other misc specfile duplication cleanup

* Sun Apr  3 2005 Rik van Riel <riel@redhat.com> 2-20050403
- fix context switch between vcpus in same domain, vcpus > cpus works again

* Sat Apr  2 2005 Rik van Riel <riel@redhat.com> 2-20050402
- move initscripts to /etc/rc.d/init.d (Florian La Roche) (#153188)
- ship only PDF documentation, not the PS or tex duplicates

* Thu Mar 31 2005 Rik van Riel <riel@redhat.com> 2-20050331
- upgrade to new xen hypervisor
- minor gcc4 compile fix

* Mon Mar 28 2005 Rik van Riel <riel@redhat.com> 2-20050328
- do not yet upgrade to new hypervisor ;)
- add barrier to fix SMP boot bug
- add tags target
- add zlib-devel build requires (#150952)

* Wed Mar  9 2005 Rik van Riel <riel@redhat.com> 2-20050308
- upgrade to last night's snapshot
- new compile fix patch

* Sun Mar  6 2005 Rik van Riel <riel@redhat.com> 2-20050305
- the gcc4 compile patches are now upstream
- upgrade to last night's snapshot, drop patches locally

* Fri Mar  4 2005 Rik van Riel <riel@redhat.com> 2-20050303
- finally got everything to compile with gcc4 -Wall -Werror

* Thu Mar  3 2005 Rik van Riel <riel@redhat.com> 2-20050303
- upgrade to last night's Xen-unstable snapshot
- drop printf warnings patch, which is upstream now

* Wed Feb 23 2005 Rik van Riel <riel@redhat.com> 2-20050222
- upgraded to last night's Xen snapshot
- compile warning fixes are now upstream, drop patch

* Sat Feb 19 2005 Rik van Riel <riel@redhat.com> 2-20050219
- fix more compile warnings
- fix the fwrite return check

* Fri Feb 18 2005 Rik van Riel <riel@redhat.com> 2-20050218
- upgrade to last night's Xen snapshot
- a kernel upgrade is needed to run this Xen, the hypervisor
  interface changed slightly
- comment out unused debugging function in plan9 domain builder
  that was giving compile errors with -Werror

* Tue Feb  8 2005 Rik van Riel <riel@redhat.com> 2-20050207
- upgrade to last night's Xen snapshot

* Tue Feb  1 2005 Rik van Riel <riel@redhat.com> 2-20050201.1
- move everything to /var/lib/xen

* Tue Feb  1 2005 Rik van Riel <riel@redhat.com> 2-20050201
- upgrade to new upstream Xen snapshot

* Tue Jan 25 2005 Jeremy Katz <katzj@redhat.com>
- add buildreqs on python-devel and xorg-x11-devel (strange AT nsk.no-ip.org)

* Mon Jan 24 2005 Rik van Riel <riel@redhat.com> - 2-20050124
- fix /etc/xen/scripts/network to not break with ipv6 (also sent upstream)

* Fri Jan 14 2005 Jeremy Katz <katzj@redhat.com> - 2-20050114
- update to new snap
- python-twisted is its own package now
- files are in /usr/lib/python now as well, ugh.

* Tue Jan 11 2005 Rik van Riel <riel@redhat.com>
- add segment fixup patch from xen tree
- fix %files list for python-twisted

* Mon Jan 10 2005 Rik van Riel <riel@redhat.com>
- grab newer snapshot, that does start up
- add /var/xen/xend-db/{domain,vnet} to %files section

* Thu Jan  6 2005 Rik van Riel <riel@redhat.com>
- upgrade to new snapshot of xen-unstable

* Mon Dec 13 2004 Rik van Riel <riel@redhat.com>
- build python-twisted as a subpackage
- update to latest upstream Xen snapshot

* Sun Dec  5 2004 Rik van Riel <riel@redhat.com>
- grab new Xen tarball (with wednesday's patch already included)
- transfig is a buildrequire, add it to the spec file

* Wed Dec  1 2004 Rik van Riel <riel@redhat.com>
- fix up Che's spec file a little bit
- create patch to build just Xen, not the kernels

* Wed Dec 01 2004 Che
- initial rpm release
