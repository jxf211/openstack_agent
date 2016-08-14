import logging
import datetime
from oslo.config import cfg
from keystoneclient.v2_0 import client as ksclient
from const import ENDPOINT_TYPE_COMPUTE, ENDPOINT_TYPE_NETWORK,\
ENDPOINT_TYPE_IMAGE, ENDPOINT_TYPE_HEAT


conf = cfg.CONF
log = logging.getLogger(__name__)

keystone_opts = [
    cfg.StrOpt('admin_user', default='',
               help="Name of Administrator"),
    cfg.StrOpt('admin_password', default='',
               help="Password of Administrator"),
    cfg.StrOpt('admin_tenant_name', default='',
               help="Tenant name of Administrator"),
    cfg.StrOpt('auth_uri', default='http://localhost:35357/v2.0',
               help="Auth uri of Keystone"),
]
conf.register_opts(keystone_opts, group="keystone")

g_client = None
g_token = None
g_endpoints = []
g_services = []
g_admin_tenant = ''


def init_keystone():
    _register_client()
    _get_all_endpoints()
    _get_all_services()


def _register_client():
    try:
        global g_client
        g_client = ksclient.Client(username=conf.keystone.admin_user,
                                   password=conf.keystone.admin_password,
                                   tenant_name=conf.keystone.admin_tenant_name,
                                   auth_url=conf.keystone.auth_uri)
    except Exception as e:
        log.error(e)
        log.error('Authorization Failed.')


def get_all_tenants():
    try:
        """ tenants = client.tenants.list()
            [<Tenant {'enabled': True, 'description': 'Admin Tenant',
                      'name': 'admin', 'id': 'f225abe80e5140c58d167ee065802'}>,
            ]
            name=tenants[i].name
            id=tenants[i].id
        """
        return g_client.tenants.list()
    except Exception as e:
        log.error(e)
        raise Exception('Error: %s' % str(e))

def get_tenants():
    try:
        tenants = []
        tenants_k = get_all_tenants()
        for tenant_k in tenants_k:
            tenant = {}
            tenant['id'] = tenant_k.id
            tenant['name'] = tenant_k.name
            tenants.append(tenant)
        return tenants
    except Exception as e:
        log.error(e)
        raise Exception('Error: %s' % str(e))


def _get_all_endpoints():
    try:
        """
            [<Endpoint {'adminurl': 'http://192.168.42.111:9696',
                        'region': 'regionOne', 'enabled': True,
                        'internalurl': 'http://192.168.42.111:9696',
                        'service_id': u'29eae15196df49b38f54058b12c6d29b',
                        'id': u'4d3ecafd14af4daf8a060982fc70c466',
                        'publicurl': u'http://192.168.42.111:9696'}>,
            ]
        """
        global g_endpoints
        g_endpoints = g_client.endpoints.list()
    except Exception as e:
        log.error(e)
        log.error('Get endpoints Failed.')


def _get_all_services():
    try:
        """
            [<Service {'type': 'network',
                       'description': 'OpenStack Networking',
                       'enabled': True,
                       'id': '29eae15196df49b38f54058b12c6d29b',
                       'name': 'neutron'}>,
            ]
        """
        global g_services
        g_services = g_client.services.list()
    except Exception as e:
        log.error(e)
        log.error('Get services Failed.')


def _get_service_id_by_type(type=None):
    for service in g_services:
        if service.type == type:
            log.debug('service(type=%s,id=%s)' % (service.type, service.id))
            return service.id
    else:
        log.warn('Not found service(type=%s)' % type)
        return None


def _get_endpoint_by_type(type=None):
    if type not in [ENDPOINT_TYPE_NETWORK, ENDPOINT_TYPE_COMPUTE,\
                     ENDPOINT_TYPE_IMAGE, ENDPOINT_TYPE_HEAT]:
        log.error('type=%s' % type)
        raise
    service_id = _get_service_id_by_type(type)
    if not service_id:
        _get_all_endpoints()
        _get_all_services()
        log.warn('Not found endpoint by type=%s' % type)
        return None
    for endpoint in g_endpoints:
        if endpoint.service_id == service_id:
            return endpoint.internalurl.strip('/')
    else:
        _get_all_endpoints()
        _get_all_services()
        log.warn('Not found endpoint by type=%s' % type)
        return None


def get_nova_endpoint():
    return _get_endpoint_by_type(ENDPOINT_TYPE_COMPUTE)

def get_neutron_endpoint():
    return _get_endpoint_by_type(ENDPOINT_TYPE_NETWORK)

def get_glance_endpoint():
    return _get_endpoint_by_type(ENDPOINT_TYPE_IMAGE)
       
def get_heat_endpoint():
    return _get_endpoint_by_type(ENDPOINT_TYPE_HEAT)

def _token_is_expired(token):
    expire = datetime.datetime.strptime(token.expires, '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.datetime.utcnow()
    # fixme
    if (expire - now) > datetime.timedelta(0, 5, 0):
        return False
    else:
        return True
    # fixme
    return True


def get_token():
    global g_token
    if g_token is None or _token_is_expired(g_token):
        g_token = g_client.tokens.authenticate(
            username=conf.keystone.admin_user,
            password=conf.keystone.admin_password,
            tenant_name=conf.keystone.admin_tenant_name,
            return_raw=False)
    log.debug('g_token=%s' % g_token.id)
    return g_token.id


def get_admin_tenant():
    tenants = get_all_tenants()
    for tenant in tenants:
        if tenant.name == conf.keystone.admin_tenant_name:
            global g_admin_tenant
            g_admin_tenant = tenant.id
            return g_admin_tenant
    else:
        log.error('admin tenant(%s) is not found' % conf.admin_tenant_name)
        return ''
