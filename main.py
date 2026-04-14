import datetime
import os.path

import yaml
from bs4 import BeautifulSoup as bs
from exchangelib import Account, Credentials, Configuration, NTLM, DELEGATE
from urllib3 import disable_warnings
import requests

class Configs:
    def __init__(self):
        self.primary_address = None
        self.chat_id = None
        self.telega_api = None
        self.host = None
        self.port = None
        self.user = None
        self.username = None
        self.password = None
        self.body_length = None
        self.current_path = None

    def set_conf(self, data):
        self.primary_address = data['primary_address']
        self.chat_id = data['chat_id']
        self.telega_api = data['telega_api']
        self.host = data['host']
        self.port = data['port']
        self.user = data['user']
        self.username = data['username']
        self.password = data['password']
        self.body_length = data['body_length']
        self.current_path = data['current_path']

Config = Configs()

def read_conf():
    try:
        with open('./config.yml', 'r') as f:
            data = yaml.safe_load(f)
            Config.set_conf(data)
            return data
    except FileNotFoundError:
        print('Config file not found')
    except Exception as e:
        print(f"Smth goes wrong: {e}")
    return None

def parse_body(bodyk):
    if not bodyk:
        return ""
    soup = bs(bodyk, 'html.parser')
    ps = soup.find_all('p', {'class': 'MsoNormal'})
    full_text = [p.text for p in ps if not p.text.replace('\n', ' '.strip()).startswith('From') and not p.text.replace('\n', ' '.strip()).startswith('Тел')]
    result = ''
    for txt in full_text:
        if 'Инфoрмация, переданная в данном электронном сообщении' in txt:
            continue
        if 'С уважением,' in txt:
            continue
        if 'данные. Любой просмотр' in txt:
            continue
        if 'просим уведомить отправителя об этом посредством' in txt:
            continue
        result += txt
    # print(result.replace('\n', ' ').strip()[:body_length])
    return result.replace('\n', ' ').strip()[:Config.body_length]

def send_msg(text):
    retry = 3
    while retry:
        try:
            resp = requests.post(Config.telega_api, data={'chat_id': Config.chat_id, 'text': text, 'parse_mode': 'HTML'}, verify=False)
            print(resp.status_code)
            break
        except:
            retry = retry - 1


def get_last_id(iid=None):
    if iid is None:
        with open(os.path.join(Config.current_path, 'prod.txt'), 'r') as f:
            data = f.read()
        return data
    with open(os.path.join(Config.current_path, 'prod.txt'), 'w') as f:
        f.write(iid)
    return iid


def test():
    if read_conf() is None:
        return
    account = Account(
        primary_smtp_address=f'{Config.username}@{Config.primary_address}',
        credentials=Credentials(username=Config.user, password=Config.password),
        config=Configuration(server=Config.host, credentials=Credentials(username=Config.user, password=Config.password), auth_type=NTLM),
        autodiscover=False,
        access_type=DELEGATE
    )
    last_id = get_last_id()
    item = account.inbox.all().order_by('-datetime_received')[0]
    if item.id != last_id:
        with open(os.path.join(Config.current_path, 'prod.html'), 'w', encoding='utf-8') as f:
            f.write(item.body)
        with open(os.path.join(Config.current_path, 'prod.html'), 'r', encoding='utf-8') as f:
            bodyk = f.read()
        text = f"<b>Новое письмо!</b>\n<b>От:</b>     <code>{item.sender.name}</code>\n" \
               f"<b>Тема:</b> <code>{item.subject}</code>\n" \
               f"<b>Время:</b> {(item.datetime_received + datetime.timedelta(hours=5)).strftime('%d.%m.%Y %H:%M')}\n" \
               f"<b>Тело:</b> <code>{parse_body(bodyk)}</code>\n"
        send_msg(text)
        print(text[:160])
        get_last_id(iid=item.id)


if __name__ == '__main__':
    disable_warnings()
    test()
