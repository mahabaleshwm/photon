# Got the intial spec from Fedora and modified it
Summary:        Easy-to-use OO interface to DBI
Name:           perl-DBIx-Simple
Version:        1.37
Release:        2%{?dist}
License:        Public Domain
Group:          Development/Libraries
Source0:        https://cpan.metacpan.org/authors/id/J/JU/JUERD/DBIx-Simple-%{version}.tar.gz
%define sha1 DBIx-Simple=7ca4c4ed5c1b6a8f32734e7d5692750b4e01aa17
URL:            http://search.cpan.org/dist/DBIx-Simple/
Vendor:         VMware, Inc.
Distribution:   Photon
BuildArch:      noarch
BuildRequires:  perl-DBI
BuildRequires:  perl
Requires:       perl
Requires:       perl-Object-Accessor
Requires:       perl-DBI

%description
DBIx::Simple provides a simplified interface to DBI, Perl's powerful
database module.

%prep
%setup -q -n DBIx-Simple-%{version}

%build
%{__perl} Makefile.PL INSTALLDIRS=vendor
make %{?_smp_mflags}

%install
make pure_install PERL_INSTALL_ROOT=%{buildroot}

find %{buildroot} -type f -name .packlist -exec rm -f {} \;
find %{buildroot} -depth -type d -exec rmdir {} 2>/dev/null \;

%{_fixperms} %{buildroot}/*

%check
make test

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{perl_vendorlib}/*
%{_mandir}/man3/*

%changelog
*   Thu Aug 20 2020 Dweep Advani <dadvani@vmware.com> 1.37-2
-   Rebuilding for perl 5.30.1
*   Fri Sep 21 2018 Dweep Advani <dadvani@vmware.com> 1.37-1
-   Update to version 1.37
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 1.35-2
-   GA - Bump release of all rpms
*   Fri Apr 3 2015 Divya Thaluru <dthaluru@vmware.com> 1.35-1
-   Initial version.
