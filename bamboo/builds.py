# coding: utf-8

# $Id: $
import json
from jira.client import JIRA, translate_resource_args
from jira.utils import raise_on_error
from bamboo.helpers import parse_config


class Builds(object):
    def __init__(self, configfile='bamboo.cfg'):
        self.jira_user = 'bamboo'
        self.jira_password = 'bamboo'
        self.server_name = 'http://bamboo.rutube.ru:8085'
        parse_config(self, configfile)
        self.jira = JIRA({'server': self.server_name, 'rest_api_version': '1.0'},
                         basic_auth=(self.jira_user, self.jira_password))

    @translate_resource_args
    def add_comment(self, build, body):
        data = {
            'author': self.jira_user,
            'content': body
        }
        url = self.jira._get_url('result/' + build + '/comment')
        r = self.jira._session.post(url, headers={'content-type':'application/json'}, data=json.dumps(data))
        raise_on_error(r)

    @translate_resource_args
    def run_plan(self, plan, **extra_variables):
        params = None
        if extra_variables:
            params = {}
            for k, v in extra_variables.items():
                params['bamboo.variable.%s' % k] = v
        url = self.jira._get_url('queue/%s' % plan)
        print "POST %s" % url
        r = self.jira._session.post(url, headers={'content-type':'application/json'},
                                    params=params, data=json.dumps({}))
        raise_on_error(r)
