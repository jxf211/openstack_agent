#!/user/bin/python
# -*- coding:utf-8 -*-
import requests
import os
import json
import time
url =  "http://172.31.0.11:20019/v1/images"
def get_glance_image_list():
    headers = {'content-type': 'application/json'}
    try:
        print url
        r = requests.get(url, headers = headers, verify=False)
	print r
	resp = r.json()
        if resp['OPT_STATUS'] != 'SUCCESS':
            print 'failed'
            print r.text
        else:
            print 'SUCCESS'
            print r.text
    except Exception as e:
        print "Exception"
        print r.text

def get_nova_flavors():
    url =  "http://172.31.0.11:20019/v1/flavors"
    headers = {'content-type': 'application/json'}	
    try:
        print url
        r = requests.get(url, headers = headers, verify=False)
        print r
        resp = r.json()
        if resp['OPT_STATUS'] != 'SUCCESS':
            print 'failed'
            print r.text
        else:
            print 'SUCCESS'
            print r.text
    except Exception as e:
        print "Exception"
        print r.text
        print e
vm_json={
    "name":"test_vm-7.20",
    "image":"d578f69c-9071-4df9-867e-d875a0a9bdb9",
    "flavor":"2",
    "tenant_id":"2246ba3feefc48a3860730e32a43c665"
    }
vmdata_json={
    "server": {
        "name":"test_vm_7.21",
        "imageRef":"d578f69c-9071-4df9-867e-d875a0a9bdb9",
        "flavorRef":"87b7e97f-0e8b-45a0-9d51-b5b5a055ab6a",
        #"max_count": 1,
        #"min_count": 1,
        "networks":[{"uuid":"5a1c75e8-afbe-4895-9f0e-bd28beb4c3eb"}]
        }
    }
def create_vm():
    url = "http://172.31.0.11:20019/v1/vm"
    headers = {'content-type': 'application/json'}
    payload = json.dumps(vmdata_json)
    try:
        print url
        r = requests.post(url, payload, headers = headers)
        resp = r.json()
        print r
        print resp    
    except Exception as e:
        print "Exception"
        print r.text
        print e

delete_json = {
    "vmid1":"a20788a0-652a-4637-89aa-19cf7dae9ebb"
    }        
def delete_vm():
    url = "http://172.31.0.11:20019/v1/vm/4248f335-fadf-41d9-a16c-ec7c3b1bbf63"
    headers = {'content-type': 'application/json'}
    
    try:
        print url
        r = requests.delete(url, headers = headers)
        print r
    except Exception as e:
        print "Exception"
        print e
network= {
    "network":
        {    
            "name": "net-name",
            "admin_state_up": "true"
        } 
    } 
def create_network():
    url = "http://172.31.0.11:20019/v1/networks"
    headers = {'content-type': 'application/json'}
    payload = json.dumps(network)
    try:
        print url 
        r = requests.post(url, payload, headers = headers) 
        print r.text
    except Exception as e:
        print "exception"
        print e

def delete_network():
    url = \
    "http://172.31.0.11:20019/v1/networks/5ac93f71-e791-442d-affb-23ca5a47ee14"
    headers = {'content-type': 'application/json'}
    try:
        print url 
        r = requests.delete(url, headers = headers) 
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e
subnet = {
        "subnet":{
            "network_id":"587e2b3c-6b74-4396-86eb-b5801559ef94",
            "ip_version": 4,
            "cidr":"10.10.40.0/24",
            }
    }          
def create_subnet():
    url = "http://172.31.0.11:20019/v1/subnets/"
    headers = {'content-type': 'application/json'}
    payload = json.dumps(subnet)
    
    try:
        print url
        r= requests.post(url, payload, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e 
def delete_subnet():
    url = \
    "http://172.31.0.11:20019/v1/subnets/24d88d11-589c-49ca-8089-39969bd76b7f"
    headers={'content-type': 'application/json'}
    
    try:
        print url 
        r = requests.delete(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e 

port = { 
     "port":{
        "network_id":"587e2b3c-6b74-4396-86eb-b5801559ef94",
        "name":"private-port",
        "admin_state_up":"true",
        }
    }

def create_port():
    url = "http://172.31.0.11:20019/v1/ports/" 
    headers = {'content-type': 'application/json'}
    payload = json.dumps(port)
    
    try:
        print url
        r= requests.post(url, payload, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e 

def delete_port():
    url="http://172.31.0.11:20018/v1/ports/f13e7c1a-5a8b-4a0a-beed-c7813fe88064"
    headers = {'content-type': 'application/json'}
    
    try:
        print url
        r = requests.delete(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e    
stack = {
       "files": {},
        "disable_rollback": "false",
       
        "stack_name": "teststack",
        "parameters": {
                "flavor":"m1.small"
        },

        "template": {
            "heat_template_version": "2013-05-23",
            #"AWSTemplateFormatVersion": "2010-09-09",
            "description": "Simple template to test heat commands",
            "parameters": {
                "flavor": {
                    "default": "m1.tiny",
                    "type": "string"
                    }
                },

                "resources": {
                    "private_net": {
                        "type":"OS::Neutron::Net",
                        "properties":{
                            "name":"private_net" 
                        }  
                    },
                   "private_subnet":{
                       "type":"OS::Neutron::Subnet",
                                "properties":{
                                    "name":"private_subnet",
                                    "network_id":{"Ref":"private_net"},
                                    "cidr":"10.20.30.0/24"
                                }
                        },
                    "hello_world1": {
                        "type": "OS::Nova::Server",
                        "properties": {
                           # "key_name": "heat_key",
                            "flavor": {
                                "get_param": "flavor"
                            },
                        "image": "d578f69c-9071-4df9-867e-d875a0a9bdb9",
                       # "networks":[{"network":"08aa8aa3-2e9e-4fcc-87fa-ea5ccbf8dde2"}]
                        "networks":[{"network":{"Ref":"private_net"}}]
                    }
                        },
        
                    "hello_world2": {
                        "type": "OS::Nova::Server",
                        "properties": {
                           # "key_name": "heat_key",
                            "flavor": {
                                "get_param": "flavor"
                            },
                        "image": "d578f69c-9071-4df9-867e-d875a0a9bdb9",
                        "networks":[{"network":{"Ref":"private_net"}}]
                        }   
                    },
                    
                    "hello_world3": {
                        "type": "OS::Nova::Server",
                        "properties": {
                           # "key_name": "heat_key",
                            "flavor": {
                                "get_param": "flavor"
                            },
                        "image": "d578f69c-9071-4df9-867e-d875a0a9bdb9",
                        "networks":[{"network":{"Ref":"private_net"}}]
                    }
                }
            }
        },
        "timeout_mins":60
    }
stack_json = {
       "files": {},
        "disable_rollback": "false",
       
        "stack_name": "teststack",

        "template": {
            "heat_template_version": "2013-05-23",
            "description": "Simple template to test heat commands",

                "resources": {
                    "private_net": {
                        "type":"OS::Neutron::Net",
                        "properties":{
                            "name":"private_net" 
                        }  
                    },
                   "router": {
                       "type":"OS::Neutron::Router",
                        "properties":{\
                            "external_gateway_info":{"network":"047404b0-295e-4f2f-be15-7644c0d79e7b"}
                        }
                   },
                   "router_interface":{
                        "type":"OS::Neutron::RouterInterface",
                        "properties":{
                                "router_id":{"Ref":"router"},
                                "subnet_id":{"Ref":"private_subnet"}
                            }  
                       },
                   "private_subnet":{
                       "type":"OS::Neutron::Subnet",
                                "properties":{
                                    "name":"private_subnet",
                                    "network_id":{"Ref":"private_net"},
                                    "cidr":"10.20.30.0/24"
                                }
                        },
                    "server_port":{
                        "type": "OS::Neutron::Port",
                            "properties":{
                                "network_id":{"Ref":"private_net"},    
                                "fixed_ips":[{"subnet_id":{"Ref":"private_subnet"}}]
                            }

                        },
                    "server_floating_ip":{
                        "type":"OS::Neutron::FloatingIP",
                            "properties":{
                                "floating_network_id":"047404b0-295e-4f2f-be15-7644c0d79e7b",
                                "port_id":{"Ref":"server_port"}
                               }
                        },
                    "hello_world1": {
                        "type": "OS::Nova::Server",
                        "properties": {
                           # "key_name": "heat_key",
                            "flavor": "m1.small",
                        "image": "d578f69c-9071-4df9-867e-d875a0a9bdb9",
                        #"networks":[{"network":"60da8ac2-2169-4e04-b00a-78b5d688522c"}]
                        #"networks":[ {"network" : {"Ref":"private_subnet"}},\
                        #"networks" :[{"network": {"Ref":"private_subnet"}}]
                        "networks":[{"port":{"Ref":"server_port"}}]
                        }
                    },
     
                    "hello_world2": {
                        "type": "OS::Nova::Server",
                        "properties": {
                           # "key_name": "heat_key",
                            "flavor": "m1.small",
                        "image": "d578f69c-9071-4df9-867e-d875a0a9bdb9",
                        "networks":[{"network":{"Ref":"private_net"}}]
                        }   
                    },
            
             }
        },
        #"outputs":{
         #       "private_ip":{"value":{"get_attr":{"hello_world1":"first_address"}}}
          #  },
        "timeout_mins":60
    }

vmjson = {
        "name": "teststack4",
        "images":[
            #{"id":"d578f69c-9071-4df9-867e-d875a0a9bdb9", "name":"vm1",\
            #   "isp":1},
            #{"id": "d578f69c-9071-4df9-867e-d875a0a9bdb9", "name":"vm2"},
            #{"id": "d578f69c-9071-4df9-867e-d875a0a9bdb9"},
            #{"id": "d578f69c-9071-4df9-867e-d875a0a9bdb9"},
            #{"id": "d578f69c-9071-4df9-867e-d875a0a9bdb9"},
        ]
    }
def create_stack():
    url = "http://172.31.0.11:20018/v1/stack/" 
    headers = {'content-type': 'application/json'}
    payload = json.dumps(vmjson)
    print payload 
    try:
        print url
        r= requests.post(url, payload, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e 
        print r.text
def get_stack():
    url = \
    "http://172.31.0.11:20019/v1/stack/teststack4"
    headers = {'content-type': 'application/json'} 
    try:
        r=requests.get(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e
        print r.text
def delete_stack():
    url = "http://172.31.0.11:20018/v1/stack/teststack4"
    headers = {'content-type': 'application/json'}
    
    try:
        r=requests.delete(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:           
        print "exception"
        print e
        print r.text
def get_stackres():
    url = \
    "http://172.31.0.11:20019/v1/stack/jingqi5979d57c9e6bb35249f65833a575c3c3/resources"
    headers = {'content-type': 'application/json'}
    try:
        r=requests.get(url, headers = headers)
        print r.text
        print r.status_code
        print r.headers
        print r
    except Exception as e:
        print "exception"
        print e
        print r.text    
vnc_json={
        "os-getVNCConsole": {
            "type": "novnc"
            }
    }
def get_vnc():
    url = \
    "http://172.31.0.11:20019/v1/servers/77adef69-71e1-4d07-8dfe-0cf3d76ecb44"
    headers = {'content-type': 'application/json'}
    try:
        payload = json.dumps(vnc_json)
        r=requests.post(url, data = payload, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e
        print r.text    
def get_info():
    url = "http://172.31.0.11:20019/v1/info"
    headers = {'content-type': 'application/json'}
    try:
        r = requests.get(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"

def get_host():
    url = "http://172.31.0.11:20019/v1/nsp/host/172.31.0.21"
    headers = {'content-type': 'application/json'}
    try:
        r = requests.get(url, headers = headers)
        print r.text
        print r.status_code
    except Exception as e:
        print "exception"
        print e

if __name__ == '__main__':
    get_glance_image_list()
    get_nova_flavors()
    #create_vm()
    #delete_vm()
    #create_network()
    #delete_network()
    #create_subnet()
    #delete_subnet()
    #create_port()
    #delete_port()
    #create_stack()
   #print "#"*40
   # time.sleep(10)
    #while True:
    #get_stack()
     #   time.sleep(5)
    #time.sleep(2)
    #print "#"*40
    #get_stackres()
    #print "#"*40
    #time.sleep(3)
    #delete_stack()
    #get_vnc()
    get_info()
    get_host()
