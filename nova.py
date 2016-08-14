# -*- coding:utf-8 -*-

import logging
from keystone import get_nova_endpoint
from keystone import get_admin_tenant
from http import req_get, req_post, req_delete
import json
from oslo.config import cfg
from const import HTTP_CHECK_OK
from webob import exc

log = logging.getLogger(__name__)
conf = cfg.CONF

def _get_url():
    url = None
    endpoint = get_nova_endpoint()
    admin_tenant_id = get_admin_tenant()
    if endpoint and admin_tenant_id:
        url = (endpoint % {'tenant_id': admin_tenant_id})
    return url

class NovaController(object):
    def __init__(self):
        self._url = self.get_url()
    
    def default(self, req, **kwargs):
        raise exc.HTTPNotFound()
    
    def get_url(self):
        try:
            end_point = get_nova_endpoint()
            admin_tenant_id = get_admin_tenant()
            if end_point and admin_tenant_id:
                url = (end_point % {'tenant_id': admin_tenant_id})  
            else:
                raise Exception('Get glance url failed')
            return url 
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def create_vm(self, req=None, **kwargs):
        try:
            code, resp = req_post(self._url +'/servers', req.body)
            return code, resp
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)
        
    def get_flavors(self, req=None, **kwargs):
        try:
            return req_get(self._url + '/flavors')
        except Exception as e:
            log.error(e)
            raise Exception

    def delete_vm(self, req=None, vmuuid=None, **kwargs):
        try:
            url = self._url + '/servers/'+ vmuuid
            return req_delete(url)
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)
    
    def get_vmdata(self, vm_uuid=None):
        try:
            url =self._url + '/servers/'+ vm_uuid
            code, resp = req_get(url)

            vmdata={}      
            if code in HTTP_CHECK_OK and "server" in resp:
                for key, value in resp["server"].iteritems():
                    if key == "addresses":
                        vmdata[key] = value
                    if key == "image":
                        vmdata[key] = value
                    if key == 'id':
                        vmdata[key] = value
            return code, vmdata
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def get_vnc_console(self, req=None, vm_uuid=None, **kwargs):
        try:
            log.debug("get vnc json data: %s" % req.body)
            url = self._url + '/servers/' + vm_uuid + '/action'
            return req_post(url, req.body)
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def get_vms(self=None, req=None, **kwargs):
        try:
            code, resp = req_get(self._url + '/servers/detail?all_tenants=true')
            
            vms = []
            if 'servers' in resp:
                for vm_info in resp['servers']:
                    vm = {}
                    if 'id' in vm_info:
                        vm['id'] = vm_info['id']
                    else:
                        log.error('No id in server respone')
                        continue
                    if 'name' in vm_info:
                        vm['name'] = vm_info['name']
                    else:
                        log.error('No name in server respone')
                        continue
                    if 'OS-EXT-SRV-ATTR:instance_name' in vm_info:
                        vm['label'] = vm_info['OS-EXT-SRV-ATTR:instance_name']
                    else:
                        log.error('No instance_name in server respone')
                        continue
                    if 'status' in vm_info:
                        vm['state'] = vm_info['status']
                    else:
                        log.error('No status in server respone')
                        continue
                    if 'OS-EXT-SRV-ATTR:hypervisor_hostname' in vm_info:
                        vm['launch_server'] = \
                            vm_info['OS-EXT-SRV-ATTR:hypervisor_hostname']
                    else:
                        log.error('No hypervisor_hostname in server respone')
                        continue
                    if 'tenant_id' in vm_info:
                        vm['tenant_id'] = vm_info['tenant_id']
                    else:
                        log.error('No tenant_id in server respone')
                        continue
                    vms.append(vm)

            return vms

        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)
    
    def get_all_hosts(self):
        code, resp = req_get(self._url + '/os-hypervisors')
        return resp
    def get_host_detail_by_id(self, id=1):
        code ,resp = req_get(self._url + '/os-hypervisors/%s' % id)
        return resp

