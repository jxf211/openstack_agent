# -*- coding:utf-8 -*-

import logging
import requests
from const import HTTP_OK,HTTP_CREATE_OK,HTTP_OK_NORESP, \
HTTP_INTERNAL_SERVER_ERROR, HTTP_CHECK_OK
from keystone import get_token
import json

log = logging.getLogger(__name__)

def req_get(url):
    try:
        log.debug('url=%s' % url)
        headers = {'content-type': 'application/json',
                   'X-Auth-Token': get_token()}
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code in HTTP_OK_NORESP:
            resp = {}
        else:
            resp = r.json()
        log.debug('status_code=%s' % r.status_code)
        return r.status_code, resp
    except Exception as err:
        log.error(err)
        return HTTP_INTERNAL_SERVER_ERROR, err

def req_post(url, json_body=None):
    try:
        log.debug('url=%s' % url)
        headers = {'content-type': 'application/json',
                   'X-Auth-Token': get_token()}
        r = requests.post(url, json_body, headers=headers, verify=False)
        if r.status_code in HTTP_OK_NORESP:
            resp = {}
        else:
            resp = r.json()
        log.debug('status_code=%s' % r.status_code)
        return r.status_code, resp

        '''
        if r.status_code in HTTP_CHECK_OK:
            return r.status_code, r.json()
        if r.status_code not in HTTP_OK_NORESP:
            log.error('status_code=%s' % r.status_code)
        return r.status_code, {}
        '''
    except Exception as err:
        log.error(err)
        return HTTP_INTERNAL_SERVER_ERROR, err

def req_delete(url):
    try:
        log.debug('url=%s' % url)
        headers = {'content-type': 'application/json',
                   'X-Auth-Token': get_token()}
        r = requests.delete(url, headers=headers, verify=False)
        if r.status_code in HTTP_CHECK_OK:
            return r.status_code, r.json()
        if r.status_code not in HTTP_OK_NORESP:   
            log.error('status_code=%s' % r.status_code)
        return r.status_code, {}
    except Exception as err:
        log.error(err)
        return HTTP_INTERNAL_SERVER_ERROR, err

        
