# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from copy import deepcopy
import ipaddress
import logging

from spyglass.exceptions import InvalidIntermediary

DATA_DEFAULT = "#CHANGE_ME"

LOG = logging.getLogger(__name__)


def _parse_ip(addr):
    """Validates the given ip address

    Validates addr and returns an IPAddress type object if it is a valid
    address. If it is not valid, a warning is logged and the addr parameter
    is returned.

    :param addr: The address to validate
    :return: addr as an IPAddress object or string
    """
    try:
        ipaddress.ip_network(addr)
    except ValueError:
        if addr != DATA_DEFAULT:
            LOG.warning("%s is not a valid IP address.", addr)
    return addr


class ServerList(object):
    """Model for a list of servers"""
    def __init__(self, server_list):
        """Validates a list of server IPs and creates a list of them

        :param server_list: list of strings
        """
        self.servers = []
        if type(server_list) is list:
            for server in server_list:
                self.servers.append(_parse_ip(server))
        elif type(server_list) is str:
            for server in server_list.split(','):
                self.servers.append(server.strip())
        else:
            raise ValueError(
                'ServerList expects a str or list, but got a %s',
                type(server_list))

    def __str__(self):
        """Returns server list as string for use in YAML documents"""
        return ",".join(self.servers)

    def __iter__(self):
        yield from self.servers

    def merge(self, server_list):
        """Merges a comma separated server list into the object

        This method is used to merge additional servers into the list. This is
        helpful for modifying objects with additional spyglass configs.
        """
        if type(server_list) is str:
            for addr in server_list.split(','):
                self.servers.append(_parse_ip(addr))
        elif type(server_list) is list:
            for addr in server_list:
                self.servers.append(_parse_ip(addr))


class IPList(object):
    """Model for IP addresses for a baremetal host"""
    def __init__(
            self,
            oob=DATA_DEFAULT,
            oam=DATA_DEFAULT,
            calico=DATA_DEFAULT,
            overlay=DATA_DEFAULT,
            pxe=DATA_DEFAULT,
            storage=DATA_DEFAULT):
        """Validates a list of string IPs into IPAddress objects

        :param oob: OOB IP address as string
        :param oam: OAM IP address as string
        :param calico: Calico IP address as string
        :param overlay: Overlay IP address as string
        :param pxe: PXE IP address as string
        :param storage: Storage IP address as string
        """
        self.oob = _parse_ip(oob)
        self.oam = _parse_ip(oam)
        self.calico = _parse_ip(calico)
        self.overlay = _parse_ip(overlay)
        self.pxe = _parse_ip(pxe)
        self.storage = _parse_ip(storage)

    def __iter__(self):
        yield from {
            'oob': self.oob,
            'oam': self.oam,
            'calico': self.calico,
            'overlay': self.overlay,
            'pxe': self.pxe,
            'storage': self.storage
        }.items()

    def set_ip_by_role(self, role: str, new_value):
        # TODO(ian-pittwood): use setattr here?
        if role == 'oob':
            self.oob = _parse_ip(new_value)
        elif role == 'oam':
            self.oam = _parse_ip(new_value)
        elif role == 'calico':
            self.calico = _parse_ip(new_value)
        elif role == 'overlay':
            self.overlay = _parse_ip(new_value)
        elif role == 'pxe':
            self.pxe = _parse_ip(new_value)
        elif role == 'storage':
            self.storage = _parse_ip(new_value)
        else:
            LOG.warning('{} role is not defined for IPList.'.format(role))

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        dictionary = {}
        if self.oob:
            dictionary['oob'] = self.oob
        if self.oam:
            dictionary['oam'] = self.oam
        if self.calico:
            dictionary['calico'] = self.calico
        if self.overlay:
            dictionary['overlay'] = self.overlay
        if self.pxe:
            dictionary['pxe'] = self.pxe
        if self.storage:
            dictionary['storage'] = self.storage

        if not dictionary:
            LOG.warning('Object contains no data.')
        return dictionary

    def merge_additional_data(self, config_dict: dict):
        if 'oob' in config_dict:
            self.oob = _parse_ip(config_dict['oob'])
        if 'oam' in config_dict:
            self.oam = _parse_ip(config_dict['oam'])
        if 'calico' in config_dict:
            self.calico = _parse_ip(config_dict['calico'])
        if 'overlay' in config_dict:
            self.overlay = _parse_ip(config_dict['overlay'])
        if 'pxe' in config_dict:
            self.pxe = _parse_ip(config_dict['pxe'])
        if 'storage' in config_dict:
            self.storage = _parse_ip(config_dict['storage'])


class Host(object):
    """Model for a baremetal host"""
    def __init__(self, name, **kwargs):
        """Stores data for a baremetal host

        :param name: Host name
        :param kwargs: see below, any data not defined here will be stored
                       in the `self.data` variable

        :Keyword Arguments:
            * *rack_name* (``str``) - Parent rack name of the host
            * *host_profile* (``str``) - Host profile
            * *type* (``str``) - Host type
            * *ip* (``IPList``) - List of IP addresses for baremetal host
        """
        self.name = name
        self.rack_name = kwargs.get('rack_name', DATA_DEFAULT)
        self.type = kwargs.get('type', DATA_DEFAULT)
        self.host_profile = kwargs.get('host_profile', DATA_DEFAULT)
        self.ip = kwargs.get('ip', IPList())
        self.data = kwargs

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        return {
            self.name: {
                'host_profile': self.host_profile,
                'ip': self.ip.dict_from_class(),
                'type': self.type
            }
        }

    def merge_additional_data(self, config_dict: dict):
        if 'rack_name' in config_dict:
            self.rack_name = config_dict['rack_name']
        if 'type' in config_dict:
            self.type = config_dict['type']
        if 'host_profile' in config_dict:
            self.host_profile = config_dict['host_profile']
        if 'ip' in config_dict:
            self.ip.merge_additional_data(config_dict['ip'])
        self.data.update(config_dict)


class Rack(object):
    """Model for a baremetal rack"""
    def __init__(self, name: str, host_list: list):
        """Stores data for the top-level, baremetal rack

        :param name: Rack name
        :param host_list: list of Host objects that belong to the rack
        """
        self.name = name
        self.hosts = host_list

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        rack_as_dict = {self.name: {}}
        for host in self.hosts:
            rack_as_dict[self.name].update(host.dict_from_class())
        return rack_as_dict

    def merge_additional_data(self, config_dict: dict):
        for key, value in config_dict.items():
            exists = False
            for host in self.hosts:
                if host.name == key:
                    exists = True
                    host.merge_additional_data(value)
            if not exists:
                self.hosts.append(Host(key, **value))

    def get_host_by_name(self, name: str):
        """Gets a host on the rack by name

        :param name: Name of the host
        :return: the matching Host object or None if not found
        :rtype: Host or None
        """
        for host in self.hosts:
            if host.name == name:
                return host
        return None

    def get_host_by_type(self, host_type: str):
        """Gets host(s) on rack by role

        :param host_type: Role of the host(s) to be retrieved
        :return: list of hosts
        :rtype: list
        """
        matching_hosts = []
        for host in self.hosts:
            if host.type == host_type:
                matching_hosts.append(host)
        return matching_hosts


class VLANNetworkData(object):
    """Model for single entry of VLAN Network Data"""
    def __init__(self, name: str, **kwargs):
        """Stores single entry of VLAN Network Data

        :param name: Name of the data entry (typically matches the role)
                     ex. calico, oam, oob, pxe, etc...
        :param kwargs: see below, any data not defined here will be stored
                       in the `self.data` variable

        :Keyword Arguments:
            * *role* (``str``) - Role of the data entry, defaults to name
            * *vlan* (``str``, ``int``) - virtual LAN ID number as str or int
            * *subnet* (``list``) - list of subnet IP addresses as strings
            * *routes* (``list``) - list of routes IP addresses as strings
            * *gateway* - gateway address
            * *dhcp_start* - DHCP range start
            * *dhcp_end* - DHCP range end
            * *static_start* - static IP range start
            * *static_end* - static IP range end
            * *reserved_start* - reserved IP range start
            * *reserved_end* - reserved IP range end
        """
        self.name = name
        self.role = kwargs.get('role', self.name)
        if self.role == 'oob':
            self.vlan = None
        else:
            self.vlan = kwargs.get('vlan', None)

        self.subnet = []
        subnet = kwargs.get('subnet', [])
        if type(subnet) is list:
            for _subnet in subnet:
                self.subnet.append(_parse_ip(_subnet))
        else:
            self.subnet.append(subnet)

        self.routes = []
        routes = kwargs.get('routes', [])
        if type(routes) is list:
            for route in routes:
                self.routes.append(_parse_ip(route))
        else:
            self.routes.append(_parse_ip(routes))

        self.gateway = _parse_ip(kwargs.get('gateway', None))

        self.dhcp_start = kwargs.get('dhcp_start', None)
        self.dhcp_end = kwargs.get('dhcp_end', None)
        self.static_start = kwargs.get('static_start', None)
        self.static_end = kwargs.get('static_end', None)
        self.reserved_start = kwargs.get('reserved_start', None)
        self.reserved_end = kwargs.get('reserved_end', None)

        self.data = kwargs

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        vlan_dict = {self.role: {}}
        if self.vlan:
            vlan_dict[self.role]['vlan'] = self.vlan
        if self.subnet:
            vlan_dict[self.role]['subnet'] = self.subnet
        if self.routes:
            vlan_dict[self.role]['routes'] = self.routes
        else:
            vlan_dict[self.role]['routes'] = []
        if self.gateway:
            vlan_dict[self.role]['gateway'] = self.gateway
        if self.dhcp_start and self.dhcp_end:
            vlan_dict[self.role]['dhcp_start'] = self.dhcp_start
            vlan_dict[self.role]['dhcp_end'] = self.dhcp_end
        if self.static_start and self.static_end:
            vlan_dict[self.role]['static_start'] = self.static_start
            vlan_dict[self.role]['static_end'] = self.static_end
        if self.reserved_start and self.reserved_end:
            vlan_dict[self.role]['reserved_start'] = self.reserved_start
            vlan_dict[self.role]['reserved_end'] = self.reserved_end
        return vlan_dict

    def merge_additional_data(self, config_dict: dict):
        if 'role' in config_dict:
            self.role = config_dict['role']
        if 'vlan' in config_dict:
            self.vlan = config_dict['vlan']
        if 'subnet' in config_dict:
            self.subnet = []
            for _subnet in config_dict['subnet']:
                self.subnet.append(_parse_ip(_subnet))
        if 'routes' in config_dict:
            self.routes = []
            for _route in config_dict['routes']:
                self.routes.append(_parse_ip(_route))
        if 'gateway' in config_dict:
            self.gateway = config_dict['gateway']
        if 'dhcp_start' in config_dict:
            self.dhcp_start = config_dict['dhcp_start']
        if 'dhcp_end' in config_dict:
            self.dhcp_end = config_dict['dhcp_end']
        if 'static_start' in config_dict:
            self.static_start = config_dict['static_start']
        if 'static_end' in config_dict:
            self.static_end = config_dict['static_end']
        if 'reserved_start' in config_dict:
            self.reserved_start = config_dict['reserved_start']
        if 'reserved_end' in config_dict:
            self.reserved_end = config_dict['reserved_end']


class Network(object):
    """Model for network configurations"""
    def __init__(self, vlan_network_data: list, **kwargs):
        """Stores data for Airship network configurations

        :param vlan_network_data: a list of VLANNetworkData objects
        :param kwargs: see below, any data not defined here will be stored
                       in the `self.data` variable

        :Keyword Arguments:
            * *bgp* (``dict``) - bgp data as a dictionary
        """
        self.vlan_network_data = vlan_network_data
        self.bgp = kwargs.get('bgp', {})
        self.data = kwargs

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        network_dict = {'vlan_network_data': {}}
        if self.bgp:
            network_dict['bgp'] = self.bgp
        for vlan in self.vlan_network_data:
            network_dict['vlan_network_data'].update(vlan.dict_from_class())
        return network_dict

    def merge_additional_data(self, config_dict: dict):
        if 'bgp' in config_dict:
            self.bgp.update(config_dict['bgp'])
        if 'vlan_network_data' in config_dict:
            for key, value in config_dict['vlan_network_data'].items():
                exists = False
                for entry in self.vlan_network_data:
                    if entry.name == key:
                        exists = True
                        entry.merge_additional_data(value)
                if not exists:
                    self.vlan_network_data.append(
                        VLANNetworkData(key, **value))
        self.data.update(config_dict)

    def get_vlan_data_by_name(self, name: str):
        """Returns VLANNetworkData object with matching name

        :param name: name of the VLANNetworkData object
        :return: the matching object or None if not found
        :rtype: VLANNetworkData or None
        """
        for entry in self.vlan_network_data:
            if entry.name == name:
                return entry
        return None

    def get_vlan_data_by_role(self, role: str):
        """Returns VLANNetworkData object with matching role

        :param role: role of the VLANNetworkData object
        :return: the matching object or None if not found
        :rtype: VLANNetworkData or None
        """
        for entry in self.vlan_network_data:
            if entry.role == role:
                return entry
        return None


class SiteInfo(object):
    """Model for general site information"""
    def __init__(self, name, **kwargs):
        """Stores general site information such as location data and site name

        :param name: Name of the site
        :param kwargs: see below, any data not defined here will be stored
                       in the `self.data` variable

        :Keyword Arguments:
            * *physical_location_id* (``str, int``) - physical id location as
                    string or int
            * *state* (``str``) - state in which site resides
            * *country* (``str``) - country in which site resides
            * *corridor* (``str``) - site corridor
            * *sitetype* (``str``) - type of the site
            * *dns* (``ServerList``) - list of DNS servers for site
            * *ntp* (``ServerList``) - list of NTP servers for site
            * *domain* (``str``) - domain of the site, ex. example.com
            * *ldap* (``dict``) - dictionary of ldap configurations as shown
                    below
                * common_name (``str``)
                * domain (``str``)
                * subdomain (``str``)
                * url (``str``)
        """
        self.name = name
        self.region_name = kwargs.get('region_name', DATA_DEFAULT)
        self.physical_location_id = kwargs.get(
            'physical_location_id', DATA_DEFAULT)
        self.state = kwargs.get('state', DATA_DEFAULT)
        self.country = kwargs.get('country', DATA_DEFAULT)
        self.corridor = kwargs.get('corridor', DATA_DEFAULT)
        self.sitetype = kwargs.get('sitetype', DATA_DEFAULT)

        self.dns = kwargs.get('dns', [])
        if type(self.dns) is not ServerList:
            self.dns = ServerList(self.dns)

        self.ntp = kwargs.get('ntp', [])
        if type(self.ntp) is not ServerList:
            self.ntp = ServerList(self.ntp)

        self.domain = kwargs.get('domain', DATA_DEFAULT)
        self.ldap = kwargs.get('ldap', {})

        self.data = kwargs

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        return {
            'corridor': self.corridor,
            'country': self.country,
            'dns': {
                'servers': str(self.dns)
            },
            'domain': self.domain,
            'ldap': self.ldap,
            'name': self.name,
            'ntp': {
                'servers': str(self.ntp)
            },
            'physical_location_id': self.physical_location_id,
            'sitetype': self.sitetype,
            'state': self.state,
        }

    def merge_additional_data(self, config_dict: dict):
        if 'name' in config_dict:
            self.name = config_dict['name']
        if 'physical_location_id' in config_dict:
            self.physical_location_id = config_dict['physical_location_id']
        if 'state' in config_dict:
            self.state = config_dict['state']
        if 'country' in config_dict:
            self.country = config_dict['country']
        if 'corridor' in config_dict:
            self.corridor = config_dict['corridor']
        if 'sitetype' in config_dict:
            self.sitetype = config_dict['sitetype']
        if 'dns' in config_dict:
            self.dns = ServerList(config_dict['dns']['servers'])
        if 'ntp' in config_dict:
            self.ntp = ServerList(config_dict['ntp']['servers'])
        if 'domain' in config_dict:
            self.domain = config_dict['domain']
        if 'ldap' in config_dict:
            self.ldap.update(config_dict['ldap'])
        self.data.update(config_dict)


class SiteDocumentData(object):
    """High level model for site data"""
    def __init__(
            self,
            site_info: SiteInfo,
            network: Network,
            baremetal: list,
            storage: dict = None):
        """Stores all data for a site

        :param site_info: general site data such as location and name
        :type site_info: SiteInfo
        :param network: networking data including a list of VLAN networks and
                        other related data
        :type network: Network
        :param baremetal: a list of rack data as Rack type objects, containing
                          Host objects within them
        :type baremetal: list
        :param storage: any additional configurations for site storage
        :type storage: dict
        """
        self.site_info = site_info
        self.storage = storage
        self.network = network
        self.baremetal = baremetal

    def dict_from_class(self):
        """Creates a writeable dict structure from the object"""
        document = {
            'baremetal': {},
            'network': self.network.dict_from_class(),
            'region_name': self.site_info.region_name,
            'site_info': self.site_info.dict_from_class(),
            'storage': self.storage
        }
        for rack in self.baremetal:
            document['baremetal'].update(rack.dict_from_class())
        return document

    def merge_additional_data(self, config_dict: dict):
        if 'site_info' in config_dict:
            self.site_info.merge_additional_data(config_dict['site_info'])
        if 'storage' in config_dict:
            if not self.storage:
                self.storage = config_dict['storage']
            else:
                self.storage.update(config_dict['storage'])
        if 'network' in config_dict:
            self.network.merge_additional_data(config_dict['network'])
        if 'baremetal' in config_dict:
            for key, value in config_dict['baremetal']:
                exists = False
                for rack in self.baremetal:
                    if key == rack.name:
                        exists = True
                        rack.merge_additional_data(value)
                if not exists:
                    self.baremetal.append(Rack(key, **value))

    def get_baremetal_rack_by_name(self, name: str):
        """Return baremetal rack with matching name

        :param name: name of the baremetal rack
        :return: the Rack object or None if not found
        :rtype: Rack or None
        """
        for rack in self.baremetal:
            if rack.name == name:
                return rack
        return None

    def get_baremetal_host_by_type(self, *args):
        """Return baremetal host(s) with matching type

        :param args: type(s) of the baremetal host
        :return: Host object(s) matching the specified host_type
        :rtype: list
        """
        host_list = []
        for rack in self.baremetal:
            rack_hosts = []
            for arg in args:
                rack_hosts.extend(rack.get_host_by_type(arg))
            host_list.extend(rack_hosts)
        return host_list


def _validate_key_in_intermediary_dict(key: str, dictionary: dict):
    if key not in dictionary:
        raise InvalidIntermediary(key=key)


def site_document_data_factory(intermediary_dict: dict) -> SiteDocumentData:
    """Uses intermediary file data to create a SiteDocumentData object

    :param intermediary_dict: A loaded intermediary file dictionary
    :return: all intermediary dictionary data returned as an object
    """
    # Validate baremetal in intermediary
    _validate_key_in_intermediary_dict('baremetal', intermediary_dict)

    # Pull out baremetal data into Rack and Host objects
    rack_list = []
    for rack, hosts in intermediary_dict['baremetal'].items():
        host_list = []
        for host_name, host_data in hosts.items():
            host_ip_list = IPList(**host_data['ip'])
            host_kwargs = {
                'rack_name': rack,
                'host_profile': host_data['host_profile'],
                'type': host_data['type'],
                'ip': host_ip_list
            }
            new_host = Host(host_name, **host_kwargs)
            host_list.append(new_host)
        new_rack = Rack(rack, host_list)
        rack_list.append(new_rack)

    # Validate network in intermediary
    _validate_key_in_intermediary_dict('network', intermediary_dict)
    # Validate vlan_network_data in intermediary
    _validate_key_in_intermediary_dict(
        'vlan_network_data', intermediary_dict['network'])
    # Validate bgp in intermediary
    _validate_key_in_intermediary_dict('bgp', intermediary_dict['network'])

    # Pull out network data into Network object
    vlan_data_list = []
    for network_type, network_data in \
            intermediary_dict['network']['vlan_network_data'].items():
        vlan_data_list.append(VLANNetworkData(network_type, **network_data))
    network = Network(vlan_data_list, bgp=intermediary_dict['network']['bgp'])

    # Validate site_info in intermediary
    _validate_key_in_intermediary_dict('site_info', intermediary_dict)
    # Validate dns in intermediary
    _validate_key_in_intermediary_dict('dns', intermediary_dict['site_info'])
    # Validate ntp in intermediary
    _validate_key_in_intermediary_dict('ntp', intermediary_dict['site_info'])
    # Validate region_name in intermediary
    _validate_key_in_intermediary_dict('region_name', intermediary_dict)

    # Pull out site_info into a SiteInfo object
    dns_server_list = ServerList(
        intermediary_dict['site_info']['dns']['servers'].split(','))
    ntp_server_list = ServerList(
        intermediary_dict['site_info']['ntp']['servers'].split(','))
    site_info_dict = deepcopy(intermediary_dict['site_info'])
    site_info_dict.pop('dns')
    site_info_dict.pop('ntp')
    site_info_dict['dns'] = dns_server_list
    site_info_dict['ntp'] = ntp_server_list
    site_info_dict['region_name'] = intermediary_dict['region_name']
    site_info = SiteInfo(**site_info_dict)

    # Validate storage in intermediary
    _validate_key_in_intermediary_dict('storage', intermediary_dict)

    # Create and return SiteDocumentData object
    site_document_data = SiteDocumentData(
        site_info=site_info,
        network=network,
        baremetal=rack_list,
        storage=intermediary_dict['storage'])
    return site_document_data
