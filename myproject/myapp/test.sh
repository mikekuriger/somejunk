# for testing 

export GOVC_URL=https://st1vccomp01a.corp.pvt	
export GOVC_USERNAME=mk7193
export GOVC_PASSWORD=Mrkamk2021#

export VM=st1lntmike03
export DC=st1
export VLAN=VLAN540
export MAC=$(govc vm.info -json $VM | jq -r '.virtualMachines[].config.hardware.device[] | select(.macAddress != null) | .macAddress')

export NET=10.5.32-VLAN540-DvS
export NM=25.255.252.0
export GW="${NET%%-*}.1"

#IP=$(python ./add_vm_to_dns.py --dc $DC --network $VLAN --hostname ${VM}.corp.pvt --mac $MAC 2> /dev/null)
