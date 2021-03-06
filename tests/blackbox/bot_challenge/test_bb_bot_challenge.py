#!/usr/bin/env python3
'''Test scopes with custom rules'''
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import subprocess
import os
import json
import time
import re
import requests
import pytest

try:
    from html.parser import HTMLParser
except ImportError:
    # python2 fallback
    from HTMLParser import HTMLParser

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
G_TEST_HOST = 'http://127.0.0.1:12345'
# ------------------------------------------------------------------------------
# run_command
# ------------------------------------------------------------------------------
def run_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return (p.returncode, stdout, stderr)
# ------------------------------------------------------------------------------
# setup scopez server in event mode
# ------------------------------------------------------------------------------
@pytest.fixture()
def setup_scopez_server():
    # ------------------------------------------------------
    # setup
    # ------------------------------------------------------
    l_cwd = os.getcwd()
    l_file_path = os.path.dirname(os.path.abspath(__file__))
    l_scopez_dir = os.path.realpath(os.path.join(l_file_path, '../../data/waf/conf/scopes'))
    l_an_list = os.path.realpath(os.path.join(l_file_path, '../../data/an/an-scopes.json'))
    l_conf_dir = os.path.realpath(os.path.join(l_file_path, '../../data/waf/conf'))
    l_ruleset_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/ruleset'))
    l_geoip2city_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/db/GeoLite2-City.mmdb'))
    l_geoip2ISP_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/db/GeoLite2-ASN.mmdb'))
    l_scopez_server_path = os.path.abspath(os.path.join(l_file_path, '../../../build/util/scopez_server/scopez_server'))
    l_subproc = subprocess.Popen([l_scopez_server_path,
                                  '-d', l_conf_dir,
                                  '-S', l_scopez_dir,
                                  '-l', l_an_list,
                                  '-r', l_ruleset_path,
                                  '-g', l_geoip2city_path,
                                  '-i', l_geoip2ISP_path])
    time.sleep(1)
    # ------------------------------------------------------
    # yield...
    # ------------------------------------------------------
    yield setup_scopez_server
    # ------------------------------------------------------
    # tear down
    # ------------------------------------------------------
    l_code, l_out, l_err = run_command('kill -9 %d'%(l_subproc.pid))
    time.sleep(0.5)
# ------------------------------------------------------------------------------
# setup scopez server in action mode
# ------------------------------------------------------------------------------
@pytest.fixture()
def setup_scopez_server_action():
    # ------------------------------------------------------
    # setup
    # ------------------------------------------------------
    # l_cwd = os.getcwd()
    l_file_path = os.path.dirname(os.path.abspath(__file__))
    l_geoip2city_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/db/GeoLite2-City.mmdb'))
    l_geoip2ISP_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/db/GeoLite2-ASN.mmdb'))
    l_conf_dir = os.path.realpath(os.path.join(l_file_path, '../../data/waf/conf'))
    l_bot_challenge = os.path.realpath(os.path.join(l_file_path, '../../data/bot/bot-challenges.json'))
    l_ruleset_path = os.path.realpath(os.path.join(l_file_path, '../../data/waf/ruleset'))
    l_scopez_dir = os.path.realpath(os.path.join(l_file_path, '../../data/waf/conf/scopes'))
    l_an_list = os.path.realpath(os.path.join(l_file_path, '../../data/an/an-scopes.json'))
    l_scopez_server_path = os.path.abspath(os.path.join(l_file_path, '../../../build/util/scopez_server/scopez_server'))
    l_subproc = subprocess.Popen([l_scopez_server_path,
                                  '-d', l_conf_dir,
                                  '-S', l_scopez_dir,
                                  '-l', l_an_list,
                                  '-r', l_ruleset_path,
                                  '-g', l_geoip2city_path,
                                  '-i', l_geoip2ISP_path,
                                  '-c', l_bot_challenge,
                                  '-a'])
    print('cmd: {}'.format(' '.join([l_scopez_server_path,
                                  '-d', l_conf_dir,
                                  '-S', l_scopez_dir,
                                  '-l', l_an_list,
                                  '-r', l_ruleset_path,
                                  '-g', l_geoip2city_path,
                                  '-i', l_geoip2ISP_path,
                                  '-c', l_bot_challenge,
                                  '-a'])))
    time.sleep(1)
    # ------------------------------------------------------
    # yield...
    # ------------------------------------------------------
    yield setup_scopez_server_action
    # ------------------------------------------------------
    # tear down
    # ------------------------------------------------------
    _, _, _ = run_command('kill -9 %d'%(l_subproc.pid))
    time.sleep(0.5)

class html_parse(HTMLParser):

   #Store data
   m_data = ""
   def handle_data(self, data):
        if data.startswith('function'):
            self.m_data = data
# ------------------------------------------------------------------------------
# Solve browser challenge
# TODO: This is based on assumption that the problem will be a simple addition
# operation in js. If problem changes in data file, this needs to be updated
# ------------------------------------------------------------------------------
def solve_challenge(a_html):
    l_problem_p = re.search('val =.[0-9]{3}\+[0-9]{3}', a_html)
    l_problem_vars = l_problem_p.group(0).split("=")[-1].split('+')
    l_solution = int(l_problem_vars[0]) + int(l_problem_vars[1])
    l_ectoken_p = re.search('ec_secure=(.*?)"', a_html)
    l_ectoken = l_ectoken_p.group(0)
    return 'ec_answer = ' + str(l_solution) + ';' + l_ectoken[:-1]
# ------------------------------------------------------------------------------
# test bot challenge in bot config
# ------------------------------------------------------------------------------
def test_bot_challenge_in_bot_config(setup_scopez_server_action):
    # ------------------------------------------------------
    # test for recieving a bot challenge
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    # ------------------------------------------------------
    # solve challenge
    # ------------------------------------------------------
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
    l_solution_cookies = solve_challenge(l_parser.m_data)
    # ------------------------------------------------------
    # test again with solved challenge and cookies
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r_json = l_r.json()
    #-------------------------------------------------------
    # check no event is returned
    # ------------------------------------------------------
    assert l_r_json['errors'][0]['message'] == 'OK'
    #-------------------------------------------------------
    # sleep for 3 seconds for challenge to expire
    # ------------------------------------------------------
    time.sleep(3)
    # ------------------------------------------------------
    # test with previous solved challenge, new challenge
    # should be returned
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
# ------------------------------------------------------------------------------
# test bot challenge with limits
# ------------------------------------------------------------------------------
def test_bot_challenge_with_limits(setup_scopez_server_action):
    # ------------------------------------------------------
    # test for recieving a bot challenge
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    # ------------------------------------------------------
    # solve challenge
    # ------------------------------------------------------
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
    l_solution_cookies = solve_challenge(l_parser.m_data)
    # ------------------------------------------------------
    # send the solved challenge thrice
    # rate limiting should block the request
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 403
    assert l_r.text == "ddos enforcement from bot config\n"
    # ------------------------------------------------------
    # sleep for 3 seconds for challenge and rate limiting
    # enforcement to expire
    # ------------------------------------------------------
    time.sleep(3)
    # ------------------------------------------------------
    # test with previous solved challenge, new challenge
    # should be returned
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
# ------------------------------------------------------------------------------
# test bot challenge with profile
# ------------------------------------------------------------------------------
def test_bot_challenge_with_profile(setup_scopez_server_action):
    # ------------------------------------------------------
    # test for recieving a bot challenge with attack vector
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html?a=%27select%20*%20from%20testing%27'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    # ------------------------------------------------------
    # solve challenge
    # ------------------------------------------------------
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
    l_solution_cookies = solve_challenge(l_parser.m_data)
    # ------------------------------------------------------
    # send the solved challenge with attack vector
    # should get custoem response from profile
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html?a=%27select%20*%20from%20testing%27'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 403
    assert l_r.text == 'This is profile custom response\n'
    # ------------------------------------------------------
    # send the solved challenge without attack vector
    # request should go through
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r_json = l_r.json()
    #-------------------------------------------------------
    # check no event is returned
    # ------------------------------------------------------
    assert l_r_json['errors'][0]['message'] == 'OK'
    #-------------------------------------------------------
    # sleep for 3 seconds for challenge to expire
    # ------------------------------------------------------
    time.sleep(3)
    # ------------------------------------------------------
    # test with previous solved challenge, new challenge
    # should be returned
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 401
    l_parser = html_parse()
    l_parser.feed(l_r.text)
    assert 'function' in l_parser.m_data
# ------------------------------------------------------------------------------
# test bot challenge events
# ------------------------------------------------------------------------------
def test_bot_challenge_events(setup_scopez_server):
    # ------------------------------------------------------
    # test for recieving a bot challenge
    # ------------------------------------------------------
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r_json = l_r.json()
    assert 'prod_profile' in l_r_json
    assert l_r_json['prod_profile']['challenge_status'] == "CHAL_STATUS_NO_TOKEN"
    assert l_r_json['prod_profile']['token_duration_sec'] == 3
    # ------------------------------------------------------
    # send random corrupted token
    # ------------------------------------------------------
    l_solution_cookies = 'ec_secure=d3JvbmdfdG9rZW4K;ec_answer=300'
    l_uri = G_TEST_HOST+'/test.html'
    l_headers = {'host': 'mybot.com',
                 'user-agent': 'bot-testing',
                 'Cookie': l_solution_cookies,
                 'waf-scopes-id': '0052'}
    l_r = requests.get(l_uri, headers=l_headers)
    assert l_r.status_code == 200
    l_r_json = l_r.json()
    assert 'prod_profile' in l_r_json
    assert l_r_json['prod_profile']['challenge_status'] == "CHAL_STATUS_TOKEN_CORRUPTED"
    assert l_r_json['prod_profile']['token_duration_sec'] == 3

