Summary:	advanced key-value store
Name:		redis
Version:	4.0.10
Release:	2%{?dist}
License:	BSD
URL:		http://redis.io/
Group:		Applications/Databases
Vendor:		VMware, Inc.
Distribution:   Photon
Source0:	http://download.redis.io/releases/%{name}-%{version}.tar.gz
%define sha1 redis=d2738d9b93a3220eecc83e89a7c28593b58e4909
Patch0:         redis-conf.patch
Patch1:         CVE-2019-10192.patch
BuildRequires:  gcc
BuildRequires:  systemd
BuildRequires:  make
Requires:	systemd
Requires(pre):  /usr/sbin/useradd /usr/sbin/groupadd
	
%description
Redis is an in-memory data structure store, used as database, cache and message broker.

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
make %{?_smp_mflags}

%install
install -vdm 755 %{buildroot}
make PREFIX=%{buildroot}/usr install
install -D -m 0640 %{name}.conf %{buildroot}%{_sysconfdir}/%{name}.conf
mkdir -p %{buildroot}/var/lib/redis
mkdir -p %{buildroot}/var/log/redis
mkdir -p %{buildroot}/usr/lib/systemd/system
cat << EOF >>  %{buildroot}/usr/lib/systemd/system/redis.service
[Unit]
Description=Redis in-memory key-value database
After=network.target

[Service]
ExecStart=/usr/bin/redis-server /etc/redis.conf --daemonize no
ExecStop=/usr/bin/redis-cli shutdown
User=redis
Group=redis

[Install]
WantedBy=multi-user.target
EOF

%check
#check requires tcl which is not supported in Photon OS right now.


%pre
getent group %{name} &> /dev/null || \
groupadd -r %{name} &> /dev/null
getent passwd %{name} &> /dev/null || \
useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
-c 'Redis Database Server' %{name} &> /dev/null
exit 0

%post
/sbin/ldconfig
%systemd_post  redis.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart redis.service


%files
%defattr(-,root,root)
%dir %attr(0750, redis, redis) /var/lib/redis
%dir %attr(0750, redis, redis) /var/log/redis
%{_bindir}/*
%{_libdir}/systemd/*
%config(noreplace) %attr(0640, %{name}, %{name}) %{_sysconfdir}/redis.conf

%changelog
* Thu Jul 25 2019 Kuladeep Rayalla <krayalla@vmware.com> 4.0.10-2
- Add patch for CVE-2019-10192
* Mon Jul 09 2018 Ajay Kaher <akaher@vmware.com> 4.0.10-1
- Upgrade redis to 4.0.10 to include CVE-2018-11218, and CVE-2018-11219.
* Mon Sep 18 2017 Alexey Makhalov <amakhalov@vmware.com> 3.2.8-4
- Remove shadow from requires and use explicit tools for post actions
* Wed May 31 2017 Siju Maliakkal <smaliakkal@vmware.com> 3.2.8-3
- Fix DB persistence,log file,grace-ful shutdown issues
* Tue May 16 2017 Siju Maliakkal <smaliakkal@vmware.com> 3.2.8-2
- Added systemd service unit
* Wed Apr 5 2017 Siju Maliakkal <smaliakkal@vmware.com> 3.2.8-1
- Updating to latest version
* Mon Oct 3 2016 Dheeraj Shetty <dheerajs@vmware.com> 3.2.4-1
- initial version
