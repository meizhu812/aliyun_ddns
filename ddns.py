from datetime import datetime
from json import load, loads
from time import sleep
from urllib.request import urlopen

from aliyunsdkalidns.request.v20150109.DescribeDomainRecordInfoRequest import DescribeDomainRecordInfoRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkcore.client import AcsClient


def load_configs():
    with open('conf.json', 'r') as f:
        configs = load(f)
    return configs['acs_conf'], configs['ddns_conf']


def get_ddns_ip(record_id):
    request = DescribeDomainRecordInfoRequest()
    request.set_accept_format('json')
    request.set_RecordId(record_id)
    response = client.do_action_with_exception(request)
    return loads(str(response, encoding='UTF-8'))['Value']


def update_ddns_ip(ip, a_type, rr, record_id):
    request = UpdateDomainRecordRequest()
    request.set_accept_format('json')
    request.set_Value(ip)
    request.set_Type(a_type)
    request.set_RR(rr)
    request.set_RecordId(record_id)
    client.do_action_with_exception(request)


def attempt(max_retries, ddns_conf):
    t_retry = 1
    retries = 0
    while retries < max_retries:
        try:
            current_ip = urlopen('http://ip.42.pl/raw').read().decode()
            previous_ddns_ip = get_ddns_ip(ddns_conf['RecordId'])
            if current_ip != previous_ddns_ip:
                update_ddns_ip(current_ip, ddns_conf['Type'], ddns_conf['RR'], ddns_conf['RecordId'])
                current_ddns_ip = get_ddns_ip(ddns_conf['RecordId'])
                assert current_ip == current_ddns_ip

                return 1, (previous_ddns_ip, current_ddns_ip)
            else:

                return 0, previous_ddns_ip
        except Exception as e:
            print('[{}] Some error occurred ({})'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), str(e)))
            sleep(t_retry)
            t_retry *= 2
            retries += 1
    return -1, None


_acs_conf, _ddns_conf = load_configs()
client = AcsClient(**_acs_conf)
while True:

    code, _ip = attempt(5, _ddns_conf)
    if code == -1:
        print('[{}] Possible Connection Error'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))
    elif code == 1:
        print('[{}] IP [{}] => [{}]'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), _ip[0], _ip[1]))
    elif code == 0:
        print('[{}] IP [{}] Unchanged.'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), _ip), end='\r')
    sleep(300)
