# -*- coding:utf-8 -*-

import logging
from keystone import get_glance_endpoint, get_heat_endpoint
from http import req_get, req_post, req_delete
from keystone import get_admin_tenant
import json
from oslo.config import cfg
from const import HTTP_CHECK_OK,HTTP_INTERNAL_SERVER_ERROR,HTTP_OK_NORESP
from nova import NovaController
import time
import  eventlet
from webob import exc
 
log = logging.getLogger(__name__)
conf = cfg.CONF

heat_opts = [ 
    cfg.StrOpt("subnet_cidr", default = '10.20.30.0/24',
                    help=" The vm ip to use"),
    cfg.StrOpt("vm_flavor", default = "m1.small",
                    help = "Create vm flavor"),
    cfg.StrOpt("publicnet_id", default = "047404b0-295e-4f2f-be15-7644c0d79e7b",
                    help = "public network id")
    ]
conf.register_opts(heat_opts, group="heat")

class HeatController(object): 
    def __init__(self):
        self._url = self.get_url()
        self.novacontroller = NovaController()
               
    def default(self, req=None, **kwargs):
        raise exc.HTTPNotFound()

    def get_url(self):
        try:
            url = None
            endpoint = get_heat_endpoint()
            admin_tenant_id = get_admin_tenant()
            if endpoint and admin_tenant_id:
                url = (endpoint % {'tenant_id': admin_tenant_id})
            else:
                raise Exception('Get heat url failed')
            return url
        except Exception as e:
            log.err(e)
            raise Exception('Error: %s' % e)

    def get_stack_href_url(self, resdata):
        try:
            url_data = resdata["stack"]["links"]
            for info in url_data:
                if isinstance(info, dict):
                    return  info.get("href", None)
          
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)
                
    def get_create_stack_status(self, url):
        status_progress = ["CREATE_IN_PROGRESS", "ROLLBACK_IN_PROGRESS",\
                           "DELETE_IN_PROGRESS"]
        while True:
            code , resp = req_get(url)
            if code not in HTTP_CHECK_OK  or \
                "stack" not in resp:
                break
            log.debug("STACK IN PROGRESS STATUS : %s" % resp)
            stack_data= resp["stack"]
            if "stack_status" in stack_data and \
                stack_data["stack_status"] not in status_progress:
                if stack_data["stack_status"] != "CREATE_COMPLETE":
                    code =  HTTP_INTERNAL_SERVER_ERROR
                break;
            eventlet.greenthread.sleep(4)
        return code, resp
             
    def create_stack(self, req=None, **kwargs):
        try:
            stack_data = self.convert_json_to_template(json.loads(req.body))
            #stack_data = json_data
            log.debug("CREATE STACK TEMPLATE : %s", stack_data)
            code, resp = req_post(self._url + '/stacks', stack_data)

            if code in HTTP_CHECK_OK or \
                code in HTTP_OK_NORESP:
                    call_url = self.get_stack_href_url(resp)
                    if call_url is not None:
                        code, resp = self.get_create_stack_status(call_url)
            return code, resp
        except Exception as e:
           log.error(e)
           raise Exception('Error: %s' % e)

    def convert_json_to_template(self, data):
        try:
            stackdata={}
            stackdata["disable_rollback"] = "false"
            
            if "name" in data:
                stackdata["stack_name"] = data.get("name", None)
            else:
                log.error("stack name is null")
                return
            template = {}
            stackdata["template"] = template
            template["heat_template_version"] = "2013-05-23"
            template["description"] = "Simple template to test heat commands"
           
            resources = {}
            template["resources"] = resources
            resources["private_net"] = {
                "type":"OS::Neutron::Net",
                "properties":{
                    "name":"private_net",
                    }
                }
            resources["private_subnet"] = {
                "type":"OS::Neutron::Subnet",
                "properties":{
                    "name":"private_subnet",
                    "network_id":{"Ref":"private_net"},
                    "cidr":conf.heat.subnet_cidr,
                    "dns_nameservers":["114.114.114.114"]
                    }
                }

            if "images" in data:
                image_data = data["images"]
            else:
                log.error("image is null")
                return

            vmcount = 1    
            for image in image_data:
                if "id" in image:
                    if "name" in image:
                        image_name = image["name"]
                    else:
                        image_name = "testvm" + str(vmcount)
                    if "flavor" in image:
                        image_flavor = image["flavor"]
                    else :
                        image_flavor = conf.heat.vm_flavor 
                    resources[image_name] = {
                        "type": "OS::Nova::Server",
                        "properties": {
                            "flavor": image_flavor,
                            "image": image["id"],
                            "networks":[{"network":{"Ref":"private_net"}}]
                            }    
                        }
                    if "isp" in image and image["isp"] == "1":
                        if "router" not in resources:
                           resources["router"] = {
                                "type":"OS::Neutron::Router",
                                "properties":{\
                                    "external_gateway_info":{"network":conf.heat.publicnet_id}
                                }
                            }
                        if "router_interface" not in resources:
                            resources["router_interface"] = {
                                "type":"OS::Neutron::RouterInterface",
                                "properties":{
                                    "router_id":{"Ref":"router"},
                                    "subnet_id":{"Ref":"private_subnet"}
                                    }
                                }
                        if "floating" in image and iamge["floating"] == "1":
                            resources["server_port"+str(vmcount)] = {
                                "type": "OS::Neutron::Port",
                                "properties":{
                                    "network_id":{"Ref":"private_net"},
                                    "fixed_ips":[{"subnet_id":{"Ref":"private_subnet"}}]
                                    }
                                }
                            resources["server_floating_ip"+str(vmcount)] = {
                                "type":"OS::Neutron::FloatingIP",
                                "properties":{
                                    "floating_network_id": conf.heat.publicnet_id,
                                    "port_id":{"Ref":"server_port"+str(vmcount)}
                                    }
                                }
                            
                            resources[image_name]["properties"]["networks"]=[{"port":{"Ref":"server_port"+str(vmcount)}}]
                vmcount += 1
            return json.dumps(stackdata)
                          
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def get_stack_status(self, req=None, stack_name=None, **kwargs):
        try:
            code, resp = req_get(self._url + '/stacks/'+ stack_name)
            return code, resp
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def delete_stack(self, req=None, stack_name=None, **kwargs):
        try:
            stack_id = self._get_stackid_by_stackname(stack_name)
            if stack_id is None:
                log.debug("Get stack id failed or stack null")
                return HTTP_INTERNAL_SERVER_ERROR, "Get stack id failed or stack null"
            
            return req_delete(self._url + '/stacks/'+ stack_name + '/' + stack_id)
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def _get_stackid_by_stackname(self, stack_name):
        code, resp = req_get(self._url + '/stacks/'+ stack_name)
        if "stack" in resp and "id" in resp["stack"]:
            return resp["stack"]["id"]

    def get_stack_resource(self, req=None, stack_name=None, **kwargs):
        try:
            return  self._get_vminfo_by_stackname(stack_name)
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e)

    def _get_vminfo_by_stackname(self, stack_name):
        try:
            code, resp = req_get(self._url + '/stacks/'+ stack_name + '/resources')
            vmdata={}
            if code not in HTTP_CHECK_OK:
                return code, resp
            if resp:
                vmdata = self._get_vmdata_by_stackresources(resp)

            return code, vmdata
        except Exception as e:
            log.error(e)
            raise Exception('Error: %s' % e) 

    def _get_vmdata_by_stackresources(self, data):
        vmdata={}
        if "resources" in data:
            vmdata["vms"] = []
            for infodata in data["resources"]:
                if "resource_type" in infodata and \
                    infodata["resource_type"] == "OS::Nova::Server" and \
                    "physical_resource_id" in infodata:
                    vm_id = infodata["physical_resource_id"]
                    code, resp = self.novacontroller.get_vmdata(vm_id)
                    if code in HTTP_CHECK_OK:
                        if "resource_name" in infodata:
                            resp["name"] = infodata["resource_name"]
                        vmdata["vms"].append(resp) 
                    else:
                        log.error("get vmdata faild vmid:%s", vm_id)
        return vmdata
                     
