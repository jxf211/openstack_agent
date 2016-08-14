# -*- coding:utf-8 -*-

import routes
import logging
import routes.middleware
import webob.dec
import webob.exc
from glance import GlanceController 
import six
import json
from nova import NovaController
from neutron import NeutronController
from lxml import etree
from heat import HeatController
from info import InfoController
import exception
from oslo_utils import encodeutils
import oslo_i18n as i18n
import serializers
from const import HTTP_INTERNAL_SERVER_ERROR
from host import HostController

log = logging.getLogger(__name__)

def render_response(body, status):
    """
    @body  :Response的body
    @status:Response的状态码
    """
    if not isinstance(body, str):
        body = str(body)
    # 获取body长度
    content_len = str(len(body))
    # 生成Response header
    headers = [('Content-type', 'application/json'),
               ('Content-length', content_len)]
    return webob.Response(body=body, status=status, headerlist=headers)


class DefaultMethodController(object):
    def option(self, req, allowed_methods, *args, **kwargs):
        raise webob.exc.HTTPNocontent(headers=[('Allow', allowed_methods)])

    def reject(self, req, allowed_methods, *args, **kwargs):
        raise webob.exc.HTTPMethodNotAllowed(headers=[('Allow', allowed_methods)])

def is_json_content_type(request):
    if request.method == 'GET':
        try:
            aws_content_type = request.params.get("ContentType")
        except Exception:
            aws_content_type = None
        # respect aws_content_type when both available
        content_type = aws_content_type or request.content_type
    else:
        content_type = request.content_type
    # bug #1887882
    # for back compatible for null or plain content type
    if not content_type or content_type.startswith('text/plain'):
        content_type = 'application/json'
    if (content_type in ('JSON', 'application/json')
            and request.body.startswith(b'{')):
        return True
    return False
   
class JSONRequestDeserializer(object):
    def has_body(self, request):
        if (int(request.content_length or 0) > 0 and
                is_json_content_type(request)): 
            return True
        return False
    
    def from_json(selfm, datastring):
        try:
            if len(datastring) > 100000:
                raise exception.RequestLimitExceeded()  
            return json.loads(datastring)
        except ValueError as ex:
            raise webob.exc.HTTPBadRequest(six, text_type(ex))

    def default (self, request):
        if self.has_body(request):
            return {'body': self.from_json(request.body)}
        else:
            return {} 

class Request(webob.Request):
    """Add some OpenStack API-specific logic to the base webob.Request."""
    def best_match_content_type(self):
        """Determine the requested response content-type."""
        supported = ('application/json',)
        bm = self.accept.best_match(supported)
        return bm or 'application/json'

    def get_content_type(self, allowed_content_types):
        """Determine content type of the request body."""
        if "Content-Type" not in self.headers:
            raise exception.InvalidContentType(content_type=None)

        content_type = self.content_type

        if content_type not in allowed_content_types:
            raise exception.InvalidContentType(content_type=content_type)
        else:
            return content_type

    def best_match_language(self):
        """Determines best available locale from the Accept-Language header.

        :returns: the best language match or None if the 'Accept-Language'
                  header was not available in the request.
        """
        if not self.accept_language:
            return None
        all_languages = i18n.get_available_languages('osagent')
        return self.accept_language.best_match(all_languages)

class Resource(object):
    def __init__(self, controller, deserializer, serializer=None):
        self.controller = controller
        self.deserializer = deserializer
        self.serializer = serializer

    @webob.dec.wsgify(RequestClass=Request)    
    def __call__(self, request):
        """WSGI method that controls (de)serialization and method dispatch."""
        action_args = self.get_action_args(request.environ)
        action = action_args.pop('action', None)  
        content_type = request.params.get("ContentType")

        try:
            deserialized_request = self.dispatch(self.deserializer,
                                                 action, request)
            action_args.update(deserialized_request)

            log.debug(('Calling %(controller)s : %(action)s'),
                      {'controller': self.controller, 'action': action})

            code, action_result = self.dispatch(self.controller, action,
                                               request, **action_args)
        except TypeError as err:
            log.error(('Exception handling resource: %s'), err)
            msg = ('The server could not comply with the request since '
                    'it is either malformed or otherwise incorrect.')
            err = webob.exc.HTTPBadRequest(msg)
            raise Exception("Error: %s" % err)
        except webob.exc.HTTPException as err:
            if isinstance(err, webob.exc.HTTPError):
                raise
            if isinstance(err, exception.OsagentAPIException):
                raise
            if isinstance(err, webob.exc.HTTPServerError):
                log.error(("Returning %(code)s to user: %(explanation)s"), 
                            {'code': err.code, 'explanation': err.explanation})
            raise
        except Exception as err:
            log.error(err)
            raise Exception("Error: %s" % err) 
        
        try:
            serializer = self.serializer
            if serializer is None:
                if content_type == "JSON":
                    serializer = serializers.JSONResponseSerializer()
                else:
                    serializer = serializers.XMLResponseSerializer()
            response = webob.Response(request=request)
            self.dispatch(serializer, action, response, action_result,
                          status=code)
            return response
        except Exception as err:
            log.error(err)
            raise Exception("Error:%s", err)

    def dispatch(self, obj, action, *args, **kwargs):
        """Find action-specific method on self and call it."""
        try:
            method = getattr(obj, action)
        except AttributeError:
            method = getattr(obj, 'default')
        return method(*args, **kwargs)
    
    def get_action_args(self, request_environment):
        """Parse dictionary created by routes library."""
        try:
            args = request_environment['wsgiorg.routing_args'][1].copy()
        except Exception:
            return {}

        try:
            del args['controller']
        except KeyError:
            pass

        try:
            del args['format']
        except KeyError:
            pass

        return args
 
class Router(object):
    def __init__(self, mapper):
        self.map = mapper
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                           self.map)   

    @webob.dec.wsgify
    def __call__(self, req):

        return self._router
    
    @staticmethod
    @webob.dec.wsgify
    def _dispatch(req):
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            log.debug('router not found:404')
            return webob.exc.HTTPNotFound()

        app = match['controller']
        return app
    
class API(Router):
    def __init__ (self):
        mapper = routes.Mapper()
        default_resource = Resource(DefaultMethodController(),
                                    JSONRequestDeserializer()) 
    
        def connect(controller, path_prefix, routes):
            urls = {}
            for r in routes:
                url = path_prefix + r['url']
                methods = r['method']
                if isinstance(methods, six.string_types):
                    methods = [methods]
                methods_str = ','.join(methods)
                mapper.connect(r['name'], url, controller=controller,
                               action=r['action'],
                               conditions={'method':methods_str})
                if url not in urls:
                    urls[url] = methods
                else:
                    urls[url] += methods
            for url, methods in urls.items():
                all_methods = ['HEAD', 'GET', 'POST', 'PATCH', 'DELETE']
                missing_methods = [m for m in all_methods if m not in methods]
                allowed_methods_str = ','.join(methods)
                mapper.connect(url,
                               controller=default_resource,
                               action='reject', 
                               allowed_methods=allowed_methods_str,
                               conditions={'method':missing_methods})
                if 'OPTIONS' not in methods:
                    mapper.connect(url,
                                   controller=default_resource,
                                   action='options',
                                   allowed_method=allowed_methods_str,
                                   conditions={'method', 'OPTIONS'})
            
        deserializer = JSONRequestDeserializer() 
        serializer =  serializers.JSONResponseSerializer()

        glance_resource = Resource(GlanceController(), deserializer, serializer)                         
        connect(controller = glance_resource,
                path_prefix = '/v1',
                routes = [
                    {
                        'name':'get images',
                        'url':'/images',
                        'action':'get_images',
                        'method':'GET'   
                    },   
                ] 
        )

        nova_resource = Resource(NovaController(), deserializer, serializer)
        connect(controller = nova_resource,
                path_prefix = '/v1',
                routes = [ 
                    {
                        'name':'create vm',
                        'url':'/vm',
                        'action':'create_vm',
                        'method':'POST'
                    },

                    {
                        'name':'delete vm',
                        'url':'/vm/:vmuuid',
                        'action':'delete_vm',
                        'method':'DELETE'    
                    },
                    
                    {
                        'name':'get flavors',
                        'url':'/flavors',
                        'action':'get_flavors',
                        'method':'GET'
                    },

                    {
                        'name':'get vmdata',
                        'url':'/servers/:vm_uuid',
                        'action':'get_vmdata',
                        'method':'GET'
                    },
                    
                    {
                        'name':'get vm vnc',
                        'url':'/servers/:vm_uuid',
                        'action':'get_vnc_console',
                        'method':'POST'    
                    }

                ]
        )
        
        neutron_resource = Resource(NeutronController(), deserializer, serializer) 
        connect(controller = neutron_resource, 
                path_prefix = '/v1',
                routes = [
                    {
                        'name':'create network',
                        'url':'/networks',
                        'action':'create_network',
                        'method':'POST' 
                    },
                        
                    {
                        'name':'delete network',
                        'url':'/networks/:network_uuid',
                        'action':'delete_network',
                        'method':'DELETE'    
                    },

                    {
                        'name':'create subnet',
                        'url':'/subnets/',
                        'action':'create_subnet',
                        'method':'POST'    
                    },

                    {
                        'name':'delete subnet',
                        'url':'/subnets/:subnet_uuid',
                        'action':'delete_subnet',
                        'method':'DELETE'
                    },
                        
                    {
                        'name':'create port',
                        'url':'/ports/',
                        'action':'create_port',
                        'method':'POST'
                    },
                    
                    {
                        'name':'delete port',
                        'url':'/ports/:port_uuid',
                        'action':'delete_port',
                        'method':'DELETE'    
                    } 
                ] 
        )

        heat_resource = Resource(HeatController(), deserializer, serializer)
        connect(controller = heat_resource,
                path_prefix = '/v1',
                routes = [
                    {
                        'name':'create stack',
                        'url':'/stack/',
                        'action':'create_stack',
                        'method':'POST'    
                    },
                                        {
                        'name':'get stack resource',
                        'url':'/stack/:stack_name/resources',
                        'action':'get_stack_resource',    
                        'method':'GET'
                    },

                    {
                        'name':'get stack status',
                        'url':'/stack/:stack_name/status',
                        'action':'get_stack_status',
                        'method':'GET'  
                    },
                
                    {
                        'name':'delete stack',
                        'url':'/stack/:stack_name',
                        'action':'delete_stack',
                        'method':'DELETE'
                    },


                ]
                        
        )
        
        info_controller = Resource(InfoController(), deserializer, serializer)
        connect(controller = info_controller,
                path_prefix = '/v1',
                routes = [
                    {
                        'name':'info request',
                        'url':'/info',
                        'action':'info_request',
                        'method':'GET'    
                    }
                
                ]
        )
        host_controller = Resource(HostController(), deserializer, serializer)
        connect(controller = host_controller,
                path_prefix = '/v1',
                routes = [
                    {
                        'name':'host info',
                        'url':'/nsp/host/:ip',
                        'action':'host_request',
                        'method':'GET'   
                    }    
                ]
        )
        super(API, self).__init__(mapper)
