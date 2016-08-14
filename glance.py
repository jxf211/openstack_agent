# -*- coding:utf-8 -*-

import logging
from keystone import get_glance_endpoint
from http import req_get
from webob import exc
  
class GlanceController(object):
    def __init__(self):
        self._url = self.get_url()
            	
    def default(self, req=None, **kwargs):
        raise exc.HTTPNotFound()
    
    def get_url(self):
        try:
            url = get_glance_endpoint()
            if not url:
                raise Exception('Get glance url failed')
            return url
        except Exception as e:
            log.err(e)
            raise Exception('Error: %s' % e)

    def get_images(self, req=None, **kwargs):
        try:
            return req_get(self._url + '/v2/images')
        except Exception as e:
            log.err(e)
            raise Exception('Error: %s' % e)
 
    
