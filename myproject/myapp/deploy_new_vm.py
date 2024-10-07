import subprocess
import os
import sys

# Function for getting datastore from cluster
def get_ds(cluster):
    cluster_normalized = cluster.lower().replace('-', '')
    result = subprocess.run(
        ['govc', 'datastore.cluster.info'],
        capture_output=True,
        text=True
    )
    for line in result.stdout.splitlines():
        if 'Name' in line and cluster_normalized in line:
            return line.split()[1]
    return None

def deploy_vm(cluster, vm, os_type, cpu, mem, vlan, disk):
    if vm.startswith('st1'):
        dc = 'st1'
        dns = '10.6.1.111,10.4.1.111'
        domains = 'corp.pvt dexmedia.com superpages.com supermedia.com prod.st1.yellowpages.com np.st1.yellowpages.com st1.yellowpages.com'
        if vlan == 'VLAN540':
            net = '10.5.32-VLAN540-DvS'
            nm = '255.255.252.0'
        elif vlan == 'VLAN673':
            net = '10.5.106-VLAN673-DvS'
            nm = '255.255.254.0'
        elif vlan == 'VLAN421':
            net = '10.5.4-VLAN421-DvS'
            nm = '255.255.252.0'
        else:
            print(f'{vlan} is not a valid VLAN')
            sys.exit(1)
        os.environ['GOVC_URL'] = 'https://st1vccomp01a.corp.pvt'
    else:
        dc = 'ev3'
        dns = '10.4.1.111,10.6.1.111'
        domains = 'corp.pvt dexmedia.com superpages.com supermedia.com prod.ev1.yellowpages.com np.ev1.yellowpages.com ev1.yellowpages.com'
        if vlan == 'VLAN540':
            net = '10.2.32-VLAN540-DvS'
            nm = '255.255.252.0'
        elif vlan == 'VLAN673':
            net = '10.4.106-VLAN673-DvS'
            nm = '255.255.254.0'
        elif vlan == 'VLAN421':
            net = '10.2.4-VLAN421-DvS'
            nm = '255.255.252.0'
        else:
            print(f'{vlan} is not a valid VLAN')
            sys.exit(1)
        os.environ['GOVC_URL'] = 'https://ev3vccomp01a.corp.pvt'

    os.environ['GOVC_USERNAME'] = 'mk7193'
    os.environ['GOVC_PASSWORD'] = 'Mrkamk2021#'

    # Get datastore cluster
    dsc = get_ds(cluster)
    if not dsc:
        print(f"Datastore not found for cluster {cluster}")
        sys.exit(1)

    print(f"Deploying {vm} to {cluster}")
    clone_cmd = [
        'govc', 'vm.clone', '-on=false', '-vm', os_type, '-c', str(cpu),
        '-m', str(mem), '-net', net, '-pool', f'/st1dccomp01/host/{cluster}/Resources',
        '-datastore-cluster', dsc, '-folder', '/st1dccomp01/vm/vRA - Thryv Cloud/TESTING', vm
    ]
    subprocess.run(clone_cmd)

    if disk > 100 and os_type == "SSVM-OEL8":
        print("Edit boot disk size")
        disk_cmd = ['govc', 'vm.disk.change', '-vm', vm, '-disk.name', 'disk-1000-0', '-size', '120G']
        subprocess.run(disk_cmd)
    else:
        print("Disk size is default, no resize needed")

    # Get MAC address
    print("Getting MAC address")
    mac_result = subprocess.run(['govc', 'vm.info', '-json', vm], capture_output=True, text=True)
    mac_address = None
    if mac_result.stdout:
        import json
        vm_info = json.loads(mac_result.stdout)
        devices = vm_info['virtualMachines'][0]['config']['hardware']['device']
        for device in devices:
            if 'macAddress' in device:
                mac_address = device['macAddress']
                break
    print(f"MAC address: {mac_address}")

    # Add VM to DNS
    print("Adding VM to DNS")
    ip_result = subprocess.run(
        ['python', './add_vm_to_dns.py', '--dc', dc, '--network', vlan, '--hostname', f'{vm}.corp.pvt', '--mac', mac_address],
        capture_output=True,
        text=True
    )
    ip = ip_result.stdout.strip()

    # Customize hostname and IP
    print("Customizing hostname and IP")
    gateway = net.split('-')[0] + '.1'
    subprocess.run(['govc', 'vm.power', '-off', '-force', vm])
    customize_cmd = [
        'govc', 'vm.customize', '-vm', vm, '-type', 'Linux', '-name', vm,
        '-domain', 'corp.pvt', '--mac', mac_address, '-ip', ip,
        '-netmask', nm, '-gateway', gateway, '-dns-server', dns, '-dns-suffix', domains
    ]
    subprocess.run(customize_cmd)

    # Further cloud-init steps could be added here
    # Based on your python script and commands for ISO generation etc.
    # e.g., subprocess.run([...])
    
if __name__ == '__main__':
    if len(sys.argv) != 8:
        print("Usage: script.py <cluster> <vm> <os> <cpu> <memory> <vlan> <disk>")
        sys.exit(1)

    cluster_arg = sys.argv[1]
    vm_arg = sys.argv[2]
    os_arg = sys.argv[3]
    cpu_arg = int(sys.argv[4])
    mem_arg = int(sys.argv[5]) * 1024
    vlan_arg = sys.argv[6]
    disk_arg = int(sys.argv[7])

    deploy_vm(cluster_arg, vm_arg, os_arg, cpu_arg, mem_arg, vlan_arg, disk_arg)
