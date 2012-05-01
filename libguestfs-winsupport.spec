%global debug_package %{nil}

%global         ntfsprogs_version 2.0.0
%global         ntfs_3g_version 2010.3.6

Name:           libguestfs-winsupport
Version:        1.0
Release:        7%{?dist}
Summary:        Add support for Windows guests to libguestfs

Group:          System Environment/Libraries
License:        GPLv2+
ExclusiveArch:  x86_64

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# This package shouldn't be installed without installing the base
# libguestfs package.
Requires:       libguestfs >= 1.7.17
Requires:       febootstrap-supermin-helper >= 2.11

# Needs fuse-libs (RHBZ#599300).
Requires:       fuse-libs

# Source and patches for ntfsprogs.  Try to keep this in step with Fedora.
Source10:       http://download.sf.net/linux-ntfs/ntfsprogs-%{ntfsprogs_version}.tar.bz2
Patch10:        ntfsprogs-2.0.0-build-extras-by-default.patch
Patch11:        ntfsprogs-2.0.0-mbonly-info.patch
Patch12:        ntfsprogs-2.0.0-check_volume.patch
Patch13:        ntfsprogs-2.0.0-undelete-segfault-fix.patch
Patch14:        ntfsprogs-2.0.0-avoid_crash_on_failed_readall_attr.patch
Patch15:        ntfsprogs-2.0.0-implicit-DSO-libgcrypt.patch

BuildRequires:  e2fsprogs-devel
Requires:       libgcrypt-devel, libgpg-error-devel

# Source and patches for ntfs-3g.  Try to keep this in step with Fedora.
Source20:       http://tuxera.com/opensource/ntfs-3g-%{ntfs_3g_version}.tgz
Patch20:        ntfs-3g-1.2216-nomtab.patch

BuildRequires:  fuse-devel, libattr-devel, libtool
Requires:       fuse


%description
This optional package adds support for Windows guests (NTFS) to the
base libguestfs Red Hat Enterprise Linux (RHEL) package.  This is
useful for examining Windows virtual machines running on RHEL, and for
performing V2V of Windows guests from another hypervisor to RHEL.

To enable Windows support, simply install this package.

To disable Windows support, uninstall this package.


%prep
%setup -q -c -T

bzcat %{SOURCE10} | tar xf -
pushd ntfsprogs-%{ntfsprogs_version}
%patch10 -p1
%patch11 -p1
%patch12 -p1
%patch13 -p1
%patch14 -p1
%patch15 -p1
#autoreconf -i # should run this
popd

zcat %{SOURCE20} | tar xf -
pushd ntfs-3g-%{ntfs_3g_version}
%patch20 -p1
popd


%build
pushd ntfsprogs-%{ntfsprogs_version}
%configure \
  --disable-gnome-vfs \
  --disable-ntfsmount \
  --disable-static \
  --enable-test \
  --disable-crypto
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
make %{?_smp_mflags}
popd

pushd ntfs-3g-%{ntfs_3g_version}
CFLAGS="$RPM_OPT_FLAGS -D_FILE_OFFSET_BITS=64" \
%configure \
        --disable-static \
        --disable-ldconfig \
        --with-fuse=external \
        --exec-prefix=/ \
        --bindir=/bin \
        --sbindir=/sbin \
        --libdir=/%{_lib}
make %{?_smp_mflags} LIBTOOL=%{_bindir}/libtool
popd

# Create a README file.
cat <<'EOF' > README
This optional package adds support for Windows guests (NTFS) to the
base libguestfs Red Hat Enterprise Linux (RHEL) package.  This is
useful for examining Windows virtual machines running on RHEL, and for
performing V2V of Windows guests from another hypervisor to RHEL.

The package contains NTFS programs from ntfsprogs %{ntfsprogs_version}
and NTFS FUSE filesystem support from ntfs-3g %{ntfs_3g_version}.
EOF


%install
rm -rf $RPM_BUILD_ROOT

# Install NTFS files locally, then copy the files we need into a
# static supermin appliance image.
mkdir ntfs
pushd ntfsprogs-%{ntfsprogs_version}
make install DESTDIR=$(cd ../ntfs && pwd)
popd
pushd ntfs-3g-%{ntfs_3g_version}
make install DESTDIR=$(cd ../ntfs && pwd)
popd
pushd ntfs/sbin
ln -s mount.ntfs-3g mount.ntfs
popd

rm -f files
echo . >> files
echo bin >> files
echo lib64 >> files
echo sbin >> files
echo usr >> files
echo usr/bin >> files
echo usr/lib64 >> files
echo usr/sbin >> files
pushd ntfs
find | \
  egrep '/s?bin/|/lib(64)/' >> ../files
cpio --quiet -o -H newc < ../files > ../ntfs.img
popd

# Supporting hostfiles.
cat <<'EOF' > ntfs.hostfiles
.
./usr
.%{_libdir}
.%{_libdir}/libgcrypt.so.*
.%{_libdir}/libgpg-error.so.*
./lib64
./lib64/libfuse.so.*
EOF

mkdir -p $RPM_BUILD_ROOT%{_libdir}/guestfs/supermin.d
install -m 0644 ntfs.img $RPM_BUILD_ROOT%{_libdir}/guestfs/supermin.d/
install -m 0644 ntfs.hostfiles $RPM_BUILD_ROOT%{_libdir}/guestfs/supermin.d/


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc ntfsprogs-%{ntfsprogs_version}/COPYING
%doc README
%{_libdir}/guestfs/supermin.d/ntfs.img
%{_libdir}/guestfs/supermin.d/ntfs.hostfiles


%changelog
* Mon Mar 28 2011 Richard W.M. Jones <rjones@redhat.com> - 1.0-7
- Disable debuginfo package.
  resolves: RHBZ#691555.

* Tue Mar  8 2011 Richard W.M. Jones <rjones@redhat.com> - 1.0-6
- Require libguestfs 1.7.17 (newer version in RHEL 6.1).
- Require febootstrap-supermin-helper instead of febootstrap
  resolves: RHBZ#670299.

* Thu Jul  1 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-5
- Make sure intermediate lib* directories are created in hostfiles (RHBZ#603429)

* Thu Jun  3 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-4
- Requires fuse-libs (RHBZ#599300).

* Fri May 21 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-3
- ExclusiveArch x86_64.

* Tue May 18 2010 Richard W.M. Jones <rjones@redhat.com> - 1.0-2
- Package Windows support for libguestfs.
