%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}



%define _libexecdir %{_libdir}

%define with_vixen  %{?_without_vixen: 0} %{?!_without_vixen: 1}

Summary: Xen Vixen is a "shim" allowing PV guests to run in HVM mode
Name:    xen-vixen
Version: 4.9.1
Release: 2%{?dist}
Group:   Development/Libraries
License: GPLv2+ and LGPLv2+ and BSD
URL:     https://www.xenproject.org/
Source0: http://bits.xensource.com/oss-xen/release/%{version}/xen-vixen-4.9.1-shim-vixen-1.tar.gz
Source70: xen-vixen-4.9.1-shim-vixen-1.tar.gz
Source71: pvshim-converter

Patch4001: 0001-vixen-port-of-shadow-PV-console-s-page-for-L2-DomU.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
%ifarch x86_64
# so that x86_64 builds pick up glibc32 correctly
BuildRequires: /usr/include/gnu/stubs-32.h
Requires: grub2
Requires: perl perl-JSON
Requires: python
Requires: /usr/bin/xorriso /usr/bin/mformat
%endif
Requires: grep
ExclusiveArch: x86_64 
%description

This package contains a "pv shim" binary, which allows Xen PV guests
to run in HVM mode without changes to the hypervisor or toolstack.
Doing so requires running a pv config through the included script, to
make a "boot sidecar" specific to that guest.

This is a mitigation for the Meltdown bug.  It protects the hypervisor
from the guests, but does not protect guest kernels from guest
userspace.

%prep

cd ${RPM_BUILD_DIR}
%{__tar} -zxf %{SOURCE70}
cd xen-vixen
%patch4001 -p1
make -C xen olddefconfig

%build
pushd ${RPM_BUILD_DIR}/xen-vixen
make xen
popd

%install
rm -rf %{buildroot}
ls ${RPM_BUILD_DIR}/xen-vixen/xen/xen.gz
install -D -m 644 ${RPM_BUILD_DIR}/xen-vixen/xen/xen.gz $RPM_BUILD_ROOT/%{_libexecdir}/xen/boot/xen-vixen.gz
install -D -m 755 %{SOURCE71} $RPM_BUILD_ROOT/%{_sbindir}/pvshim-converter

############ debug packaging: list files ############

find %{buildroot} -print | xargs ls -ld | sed -e 's|.*%{buildroot}||' > f1.list

############ create dirs in /var ############

mkdir -p %{buildroot}%{_localstatedir}/lib/xen/pvshim-sidecars

# Make backwards-compatibility links to /usr/lib/xen/bin
%if "%{_libdir}" != "/usr/lib"
mkdir -p %{buildroot}/usr/lib/xen/boot
pushd %{buildroot}/usr/lib/xen/boot/
ln -s ../../../lib64/xen/boot/xen-vixen.gz
%endif
popd

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)

# Avoid owning /usr/lib twice on i386
%if "%{_libdir}" != "/usr/lib"
/usr/lib/xen/boot/xen-vixen.gz
%endif
%dir %{_libexecdir}/xen/boot
%{_libexecdir}/xen/boot/xen-vixen.gz

%{_sbindir}/pvshim-converter

%changelog
* Thu Jan 18 2018 George Dunlap <george.dunlap@citrix.com> 4.9.1-2.el6.centos
- Add dependencies for the script

* Fri Jan 12 2018 George Dunlap <george.dunlap@citrix.com> 4.9.1-1.el6.centos
- Move vixen to a separate package

* Thu Jan 11 2018 Sarah Newman <srn@prgmr.com> 4.8.2-8.el6.centos
- Add Vixen related files. Includes console input, centos specific changes,
  and minor improvements to the pvshim-converter script.
- Did not apply XSA 253 as it is 4.10 only

