#!/bin/bash
#
# This is a temporary script for triggering all the pythin scripts
# 9-16-24 Mike Kuriger

# function for getting datastore from cluster
get_ds() {
    local arg=$1
    CL=$(echo ${1,,} | sed 's/-//g')
    govc datastore.cluster.info|grep Name|grep $CL |awk '{print $2}'
}

CL=$1
VM=$2
OS=$3
CPU=$4
MEM=$(($5*1024))
VLAN=$6
DISK=$7

if [[ $VM =~ ^st1 ]]; then
  DC=st1
  DNS=10.6.1.111,10.4.1.111
  DOMAINS='corp.pvt dexmedia.com superpages.com supermedia.com prod.st1.yellowpages.com np.st1.yellowpages.com st1.yellowpages.com'
  if [[ "$VLAN" = "VLAN540" ]]; then
    NET=10.5.32-VLAN540-DvS
    NM=255.255.252.0
  elif [[ "$VLAN" = "VLAN673" ]]; then
    NET=10.5.106-VLAN673-DvS
    NM=255.255.254.0
  elif [[ "$VLAN" = "VLAN421" ]]; then
    NET=10.5.4-VLAN421-DvS
    NM=255.255.252.0
  else
    echo "$VLAN is not a valid VLAN"
    exit 1
  fi
  export GOVC_URL=https://st1vccomp01a.corp.pvt	
else
  DC=ev3
  DNS=10.4.1.111,10.6.1.111
  DOMAINS='corp.pvt dexmedia.com superpages.com supermedia.com prod.ev1.yellowpages.com np.ev1.yellowpages.com ev1.yellowpages.com'
  if [[ "$VLAN" = "VLAN540" ]]; then
    NET=10.2.32-VLAN540-DvS
    NM=255.255.252.0
  elif [[ "$VLAN" = "VLAN673" ]]; then
    NET=10.4.106-VLAN673-DvS
    NM=255.255.254.0
  elif [[ "$VLAN" = "VLAN421" ]]; then
    NET=10.2.4-VLAN421-DvS
    NM=255.255.252.0
  else
    echo "$VLAN is not a valid VLAN"
    exit 1
  fi
  export GOVC_URL=https://ev3vccomp01a.corp.pvt	
fi

export GOVC_USERNAME=mk7193
export GOVC_PASSWORD=Mrkamk2021#

# deploy VM by cloning template
DSC=$(get_ds ${CL}) # datastore cluster
echo "Deploying $VM to $CL"
echo govc vm.clone -on=false -vm $OS -c $CPU -m $MEM -net $NET -pool /st1dccomp01/host/${CL}/Resources -datastore-cluster ${DSC} -folder '/st1dccomp01/vm/vRA - Thryv Cloud/TESTING' $VM

exit 0

# edit boot disk to match requested size
if [[ "DISK" -gt "100" ]] && [[ "$OS" = "SSVM-OEL8 ]]; then
  echo "edit boot disk size"
  govc vm.disk.change -vm $VM -disk.name "disk-1000-0" -size 120G
else 
  echo "Disk size is default, no resize needed"
fi

# Get mac address of VM 
echo -n "Getting mac address"
MAC=$(govc vm.info -json $VM | jq -r '.virtualMachines[].config.hardware.device[] | select(.macAddress != null) | .macAddress')
echo " - $MAC"

# add vm to DNS
echo "Adding VM to DNS"
IP=$(python ./add_vm_to_dns.py --dc $DC --network $VLAN --hostname ${VM}.corp.pvt --mac $MAC 2> /dev/null)

# make sure VM is off and customize hotname and IP
echo "Customizing hostname, and IP"
GW="${NET%%-*}.1"
govc vm.power -off -force $VM

govc vm.customize -vm $VM -type Linux -name $VM -domain corp.pvt --mac $MAC -ip $IP -netmask $NM -gateway $GW -dns-server $DNS -dns-suffix "$DOMAINS"

# create files for cloud-init, saved in cloud-init-images/${VM}/
echo "Creating ISO for cloud-init and mounting it to the VM"
DATE=$(date +%Y-%m-%dT%H:%M:%S)
CD=$(govc device.ls -vm $VM |grep cdrom | awk '{print $1}')

# this part still needs ARGS from the application form, but does work if set manually for now
python generate_iso_command.py --vm $VM --date $DATE --env Testing --builtby "Mike Kuriger" --ticket "TSM-000000" --appname "app1" --owner "Mike Kuriger" 
#python generate_iso_command.py --vm $VM --date $DATE --env $args.ENV --builtby $args.BUILTBY --ticket $args.TICKET --appname $args.APPNAME --owner $args.OWNER --mac $MAC --network $VLAN

# put files into an ISO image
genisoimage  -output cloud-init-images/${VM}/seed.iso -volid cidata -joliet -rock cloud-init-images/${VM}/user-data cloud-init-images/${VM}/meta-data 

# copy the ISO image to the VM's datastore
DS=$(govc vm.info -json $VM | jq -r '.virtualMachines[].config.hardware.device[].backing.fileName' |grep '\['|tail -1 | sed -e 's/\[//' -e 's/\]//' | awk '{print $1}')
govc datastore.upload -ds $DS ./cloud-init-images/$VM/seed.iso $VM/seed.iso

# mount the ISO to the VM and power it on
CD=$(govc device.ls -vm $VM |grep cdrom | awk '{print $1}')
govc device.cdrom.insert -vm $VM -device $CD -ds $DS ${VM}/seed.iso
govc device.connect -vm $VM $CD 
govc vm.power -on $VM