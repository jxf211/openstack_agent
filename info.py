# -*- coding:utf-8 -*-

import logging
import json
from const import HTTP_OK, HTTP_INTERNAL_SERVER_ERROR
from keystone import get_tenants
from nova import NovaController
from neutron import NeutronController
from webob import exc

log = logging.getLogger(__name__)

nova_uri = None
neutron_uri = None

class InfoController(object):
    def __init__(self):
        self.neutron = NeutronController()
        self.nova = NovaController()

    def default(self, req=None, **kwargs):
        raise exc.HTTPNotFound()
          
    def info_request(self, req=None, **kwargs):
        info = {}
        try:
            networks = self.neutron.get_networks()
            info['networks'] = networks
            subnets = self.neutron.get_subnets()
            info['subnets'] = subnets
            vms = self.nova.get_vms()
            info['vms'] = vms
            ports = self.neutron.get_ports()
            info['ports'] = ports
            tenants = get_tenants()
            info['tenants'] = tenants
            routers = self.neutron.get_routers()
            info['routers'] = routers
            return HTTP_OK, info
        except Exception as e:
            log.error(e)
            return HTTP_INTERNAL_SERVER_ERROR, str(e)
               
