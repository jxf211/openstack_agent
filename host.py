# -*- coding:utf-8 -*-

import logging
import simplejson as json
from const import HTTP_OK
from const import HTTP_BAD_REQUEST
from const import HTTP_INTERNAL_SERVER_ERROR
from nova import  NovaController
from webob import exc

log = logging.getLogger(__name__)

class HostController(object):
    def __init__(self):
        self.novacontroller = NovaController()
    
    def default(self):
        raise exc.HTTPNotFound()  
    
    def host_request(self, req=None, ip=None, **kwargs):
        try:
            log.info('entry.')
            hosts = self.novacontroller.get_all_hosts()
            for host in hosts['hypervisors']:
                host_detail = self.novacontroller.get_host_detail_by_id(host['id'])
                if host_detail['hypervisor']['host_ip'] == ip:
                    break
                else:
                    log.error('No Host (%s)' % ip)
                return HTTP_BAD_REQUEST, "{'ERROR': 'No Host (%s)'}" % ip
            return HTTP_OK, host_detail
        except Exception as e:
            log.error(str(e))
            return HTTP_INTERNAL_SERVER_ERROR, "{'ERROR': %s}" % str(e)
