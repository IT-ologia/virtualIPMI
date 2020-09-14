# virtualIPMI

virtualIPMI is a universal IPMI server that proxies ipmitool requests (based on the IPMI protocol) to shell scripts. It can be used  e.g. to manage VMs within a hypervisor...as if these VMs had a Baseboard Management Controller (BMC) inside. It runs as a container, whereby each container can manage one e.g. VM through the customized scripts. So if you want to manage X VMs, then you have to run the image appropriately X times. The supported IPMI commands are listed below.

## How to build it

1. Install docker (e.g. for CentOS use this manual: <https://docs.docker.com/engine/install/centos>).

2. Install GNU Make:

   ```bash
   sudo yum install make
   ```

3. Checkout this repository:

   ```bash
   git clone https://github.com/IT-ologia/virtualIPMI.git
   cd virtualIPMI
   ```

4. Build the image:

   ```bash
   make build
   ```

5. Run the test server:

   ```bash
   make run
   ```

## Use cases

Let's asssume that a bare metal deployment should be tested/evaluated in a virtual environment. Such a deployment could be e.g. an OpenStack one or an OpenShift User Provisioned Infrastructure and so on. These deployments actually boot a bare metal machine via PXE by using the IPMI protocol in order to set up this machine. virtualIPMI can be used in this case to proxy these IPMI commands to the shell scripts, whereby these scripts can be by customized for the appropriate hypervisor to poweron the VM, power off, reboot, and so on.

## IPMI supported commands

The server supports the following IPMI commands that are proxied to scripts in the **scripts** directory:

```bash
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power status
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power on
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power off
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power cycle
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power reset
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power diag
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 power soft
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 chassis bootparam get 5
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 chassis bootdev disk
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 chassis bootdev pxe
ipmitool -I lanplus -U admin -P admin -H localhost -p 623 chassis bootdev cdrom
```
