Summary:        Kubernetes cluster management
Name:           kubernetes
Version:        1.11.9
Release:        5%{?dist}
License:        ASL 2.0
URL:            https://github.com/kubernetes/kubernetes/archive/v%{version}.tar.gz
Source0:        kubernetes-%{version}.tar.gz
%define sha1    kubernetes-%{version}.tar.gz=a190a4ac59ac5629f3fe7b55fe9943b110e39dae
Source1:        https://github.com/kubernetes/contrib/archive/contrib-0.7.0.tar.gz
%define sha1    contrib-0.7.0=47a744da3b396f07114e518226b6313ef4b2203c
Patch0:         k8s-1.11-vke.patch
Patch1:         go-27704.patch
Patch2:         go-27842.patch
Patch3:         k8s-1.11-CVE-2019-11244.patch
Group:          Development/Tools
Vendor:         VMware, Inc.
Distribution:   Photon
BuildRequires:  go >= 1.10
BuildRequires:  rsync
BuildRequires:  which
Requires:       cni
Requires:       ebtables
Requires:       etcd >= 3.0.4
Requires:       ethtool
Requires:       iptables
Requires:       iproute2
Requires(pre):  /usr/sbin/useradd /usr/sbin/groupadd
Requires(postun):/usr/sbin/userdel /usr/sbin/groupdel
Requires:       socat
Requires:       (util-linux or toybox)
Requires:       cri-tools

%description
Kubernetes is an open source implementation of container cluster management.

%package        kubeadm
Summary:        kubeadm deployment tool
Group:          Development/Tools
Requires:       %{name} = %{version}
%description    kubeadm
kubeadm is a tool that enables quick and easy deployment of a kubernetes cluster.

%package	kubectl-extras
Summary:	kubectl binaries for extra platforms
Group:		Development/Tools
%description	kubectl-extras
Contains kubectl binaries for additional platforms.

%package        pause
Summary:        pause binary
Group:          Development/Tools
%description    pause
A pod setup process that holds a pod's namespace.

%prep -p exit
%setup -qn %{name}-%{version}
cd ..
tar xf %{SOURCE1} --no-same-owner
sed -i -e 's|127.0.0.1:4001|127.0.0.1:2379|g' contrib-0.7.0/init/systemd/environ/apiserver
cd %{name}-%{version}
%patch0 -p1

pushd vendor/golang.org/x/net
%patch1 -p1
%patch2 -p1
popd
%patch3 -p1

%build
make
pushd build/pause
mkdir -p bin
gcc -Os -Wall -Werror -static -o bin/pause-amd64 pause.c
strip bin/pause-amd64
popd
make WHAT="cmd/kubectl" KUBE_BUILD_PLATFORMS="darwin/amd64 windows/amd64"

%install
install -vdm644 %{buildroot}/etc/profile.d
install -m 755 -d %{buildroot}%{_bindir}
install -m 755 -d %{buildroot}/opt/vmware/kubernetes
install -m 755 -d %{buildroot}/opt/vmware/kubernetes/darwin/amd64
install -m 755 -d %{buildroot}/opt/vmware/kubernetes/linux/amd64
install -m 755 -d %{buildroot}/opt/vmware/kubernetes/windows/amd64

binaries=(cloud-controller-manager hyperkube kube-aggregator kube-apiserver kube-controller-manager kubelet kube-proxy kube-scheduler kubectl)
for bin in "${binaries[@]}"; do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 -t %{buildroot}%{_bindir} _output/local/bin/linux/amd64/${bin}
done
install -p -m 755 -t %{buildroot}%{_bindir} build/pause/bin/pause-amd64

# kubectl-extras
install -p -m 755 -t %{buildroot}/opt/vmware/kubernetes/darwin/amd64/ _output/local/bin/darwin/amd64/kubectl
install -p -m 755 -t %{buildroot}/opt/vmware/kubernetes/linux/amd64/ _output/local/bin/linux/amd64/kubectl
install -p -m 755 -t %{buildroot}/opt/vmware/kubernetes/windows/amd64/ _output/local/bin/windows/amd64/kubectl.exe

# kubeadm install
install -vdm644 %{buildroot}/etc/systemd/system/kubelet.service.d
install -p -m 755 -t %{buildroot}%{_bindir} _output/local/bin/linux/amd64/kubeadm
install -p -m 755 -t %{buildroot}/etc/systemd/system build/rpms/kubelet.service
install -p -m 755 -t %{buildroot}/etc/systemd/system/kubelet.service.d build/rpms/10-kubeadm.conf
sed -i '/KUBELET_CGROUP_ARGS=--cgroup-driver=systemd/d' %{buildroot}/etc/systemd/system/kubelet.service.d/10-kubeadm.conf

cd ..
# install config files
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}
install -m 644 -t %{buildroot}%{_sysconfdir}/%{name} contrib-0.7.0/init/systemd/environ/*
cat << EOF >> %{buildroot}%{_sysconfdir}/%{name}/kubeconfig
apiVersion: v1
clusters:
- cluster:
    server: http://127.0.0.1:8080
EOF
sed -i '/KUBELET_API_SERVER/c\KUBELET_API_SERVER="--kubeconfig=/etc/kubernetes/kubeconfig"' %{buildroot}%{_sysconfdir}/%{name}/kubelet

# install service files
install -d -m 0755 %{buildroot}/usr/lib/systemd/system
install -m 0644 -t %{buildroot}/usr/lib/systemd/system contrib-0.7.0/init/systemd/*.service

# install the place the kubelet defaults to put volumes
install -dm755 %{buildroot}/var/lib/kubelet
install -dm755 %{buildroot}/var/run/kubernetes

mkdir -p %{buildroot}/%{_lib}/tmpfiles.d
cat << EOF >> %{buildroot}/%{_lib}/tmpfiles.d/kubernetes.conf
d /var/run/kubernetes 0755 kube kube -
EOF

%check
export GOPATH=%{_builddir}
go get golang.org/x/tools/cmd/cover
make %{?_smp_mflags} check

%clean
rm -rf %{buildroot}/*

%pre
if [ $1 -eq 1 ]; then
    # Initial installation.
    getent group kube >/dev/null || groupadd -r kube
    getent passwd kube >/dev/null || useradd -r -g kube -d / -s /sbin/nologin \
            -c "Kubernetes user" kube
fi

%post
chown -R kube:kube /var/lib/kubelet
chown -R kube:kube /var/run/kubernetes
systemctl daemon-reload

%post kubeadm
systemctl daemon-reload
systemctl stop kubelet
systemctl enable kubelet

%preun kubeadm
if [ $1 -eq 0 ]; then
    systemctl stop kubelet
fi

%postun
if [ $1 -eq 0 ]; then
    # Package deletion
    userdel kube
    groupdel kube
    systemctl daemon-reload
fi

%postun kubeadm
if [ $1 -eq 0 ]; then
    systemctl daemon-reload
fi

%files
%defattr(-,root,root)
%{_bindir}/cloud-controller-manager
%{_bindir}/hyperkube
%{_bindir}/kube-aggregator
%{_bindir}/kube-apiserver
%{_bindir}/kube-controller-manager
%{_bindir}/kubelet
%{_bindir}/kube-proxy
%{_bindir}/kube-scheduler
%{_bindir}/kubectl
#%{_bindir}/kubefed
%{_lib}/systemd/system/kube-apiserver.service
%{_lib}/systemd/system/kubelet.service
%{_lib}/systemd/system/kube-scheduler.service
%{_lib}/systemd/system/kube-controller-manager.service
%{_lib}/systemd/system/kube-proxy.service
%{_lib}/tmpfiles.d/kubernetes.conf
%dir %{_sysconfdir}/%{name}
%dir /var/lib/kubelet
%dir /var/run/kubernetes
%config(noreplace) %{_sysconfdir}/%{name}/config
%config(noreplace) %{_sysconfdir}/%{name}/apiserver
%config(noreplace) %{_sysconfdir}/%{name}/controller-manager
%config(noreplace) %{_sysconfdir}/%{name}/proxy
%config(noreplace) %{_sysconfdir}/%{name}/kubelet
%config(noreplace) %{_sysconfdir}/%{name}/kubeconfig
%config(noreplace) %{_sysconfdir}/%{name}/scheduler

%files kubeadm
%defattr(-,root,root)
%{_bindir}/kubeadm
/etc/systemd/system/kubelet.service
/etc/systemd/system/kubelet.service.d/10-kubeadm.conf

%files pause
%defattr(-,root,root)
%{_bindir}/pause-amd64

%files kubectl-extras
%defattr(-,root,root)
/opt/vmware/kubernetes/darwin/amd64/kubectl
/opt/vmware/kubernetes/linux/amd64/kubectl
/opt/vmware/kubernetes/windows/amd64/kubectl.exe

%changelog
*   Fri Aug 30 2019 Ashwin H <ashwinh@vmware.com> 1.11.9-5
-   Bump up version to compile with new go
*   Tue Jul 14 2019 Emil John <ejohn@vmware.com> 1.11.9-4
-   Add security fixes to the patch (6716390)
*   Thu May 23 2019 Ashwin H <ashwinh@vmware.com> 1.11.9-3
-   Fix CVE-2019-11244
*   Fri May 03 2019 Bo Gan <ganb@vmware.com> 1.11.9-2
-   Fix CVE-2018-17846 and CVE-2018-17143
*   Mon Apr 01 2019 Emil John <ejohn@vmware.com> 1.11.9-1
-   VCP patch for K8s v1.11.9 (077135f)
*   Fri Feb 22 2019 abhishek rathore <arathore@vmware.com> 1.11.7-1
-   VCP patch for K8s v1.11.7 (2c62ea46)
*   Wed Feb 13 2019 Dheeraj Shetty <dheerajs@vmware.com> 1.11.6-2
-   Add VMware Cloud PKS patch (a7e6dfae)
*   Thu Jan 3 2019 Emil <ejohn@vmware.com> 1.11.6-1
-   Upgrade to 1.11.6 with VMware Cloud PKS patch (5fcf357b)
*   Tue Nov 27 2018 Amarnath <vaa@vmware.com> 1.11.5-1
-   Upgrade to 1.11.5 with VMware Cloud PKS patch (3f918d7)
*   Tue Oct 16 2018 Dheeraj Shetty <dheerajs@vmware.com> 1.11.3-2
-   Add vke patch (350444)
*   Fri Oct 05 2018 Dheeraj Shetty <dheerajs@vmware.com> 1.11.3-1
-   Upgrade to k8s version 1.11.3. Add vke patch when it is ready
*   Fri Aug 10 2018 Tapas Kundu <tkundu@vmware.com> 1.11.1-2
-   Added cri-tools as Requires. Kubeadm needs crictl provided by cri-tools.
*   Fri Aug 03 2018 Dheeraj Shetty <dheerajs@vmware.com> 1.11.1-1
-   Add k8s version 1.11.1 and vke patch
