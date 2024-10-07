from SOLIDserverRest import SOLIDserverRest
import json, logging, math, ipaddress, pprint

SDS_CON = SOLIDserverRest('st1dceipmaster.corp.pvt')
SDS_CON.set_ssl_verify(False)
SDS_CON.use_basicauth_sds(user='mk7193', password='Mrkamk2021#')


def get_space(name):
    """get a space by its name from the SDS"""
    parameters = {
        "WHERE": "site_name='{}'".format(name),
        "limit": "1"
    }

    rest_answer = SDS_CON.query("ip_site_list", parameters)

    if rest_answer.status_code != 200:
        logging.error("cannot find space %s", name)
        return None

    rjson = json.loads(rest_answer.content)
    #print(rjson)

    return {
        'type': 'space',
        'name': name,
#        'is_default': rjson[0]['site_is_default'],
        'is_template': rjson[0].get('site_is_template', 'N/A'), 
        'id': rjson[0]['site_id']
    }

def get_subnet_v4(name, space_id=None):
    parameters = {
        "WHERE": "subnet_name='{}' and is_terminal='1'".format(name),
        "TAGS": "network.gateway"
    }

    if space_id is not None:
        parameters['WHERE'] = parameters['WHERE'] + " and site_id='{}'".format(int(space_id))

    rest_answer = SDS_CON.query("ip_subnet_list", parameters)

    if rest_answer.status_code != 200:
        logging.error("cannot find subnet %s", name)
        return None

    rjson = json.loads(rest_answer.content)

    print(rjson)
    
    return {
        'type': 'terminal_subnet',
        'dc': 'parent_subnet_name',        
        'name': name,
        'addr': rjson[0]['start_hostaddr'],
        'cidr': 32-int(math.log(int(rjson[0]['subnet_size']), 2)),
        'gw': rjson[0]['tag_network_gateway'],
        'used_addresses': rjson[0]['subnet_ip_used_size'],
        'free_addresses': rjson[0]['subnet_ip_free_size'],
        'space': rjson[0]['site_id'],
        'id': rjson[0]['subnet_id']
    }

space = get_space("thryv-eip-ipam")
# ST1
subnet = get_subnet_v4("vlan 421- linux_421", space_id=space['id'])        # 10.5.4-VLAN421-DvS   (code finds the same VLAN in EV3 instead)
#subnet = get_subnet_v4("ST1 - Weblogic", space_id=space['id'])             # 10.5.32-VLAN540-DvS  'addr': '10.5.32.0', 'cidr': 22
# EV3
#subnet = get_subnet_v4("vlan673_vmware_management", space_id=space['id'])  # 10.4.106-VLAN673-DvS  'addr': '10.5.106.0', 'cidr': 23
#subnet = get_subnet_v4("EV3 - Weblogic", space_id=space['id'])             # 10.2.32-VLAN540-DvS  'addr': '10.2.32.0', 'cidr': 22
#subnet = get_subnet_v4("vlan 421- linux_421", space_id=space['id'])        # 10.2.4-VLAN421-DvS   'addr': '10.2.4.0', 'cidr': 22

print(subnet)

def get_next_free_address(subnet_id, number=1, start_address=None):
    parameters = {
          "subnet_id": str(subnet_id),
          "max_find": str(number),
          "begin_addr": "10.5.4.1",
    }

    if start_address is not None:
        parameters['begin_addr'] = str(ipaddress.IPv4Address(start_address))

    rest_answer = SDS_CON.query("ip_address_find_free", parameters)

    if rest_answer.status_code != 200:
        logging.error("cannot find subnet %s", name)
        return None

    rjson = json.loads(rest_answer.content)

    result = {
           'type': 'free_ip_address',
           'available': len(rjson),
           'address': []
    }

    for address in rjson:
        result['address'].append(address['hostaddr'])

    return result

ipstart = ipaddress.IPv4Address(subnet['addr']) # +100
free_address = get_next_free_address(subnet['id'], 5, ipstart)
pprint.pprint(free_address)


del(SDS_CON)