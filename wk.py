
from sys import stderr
from flask import session
import requests

def get_wk_username(wk_token: str) -> str | None:
    
    if wk_token == '':
        return None
    base_url = 'https://api.wanikani.com/v2/'
    headers = {'Authorization': 'Bearer ' + wk_token}
    try:
        wk_data = get_wk_data_from_url(base_url + 'user', headers)
    except AssertionError:
        print('Failed to get WK vocabulary', file=stderr)
        return None
    return wk_data[0]['username']

def get_gurued_vocab(wk_token: str) -> list[str] | None:
    
    if wk_token == '':
        return None
    base_url = 'https://api.wanikani.com/v2/'
    headers = {'Authorization': 'Bearer ' + wk_token}
    try:
        wk_data = get_wk_data_from_url(base_url + 'subjects?types=vocabulary', headers)
    except AssertionError:
        print('Failed to get WK vocabulary', file=stderr)
        return None
    try:
        gurued_data = get_wk_data_from_url(base_url + 'assignments?subject_types=vocabulary&srs_stages=6,7,8,9', headers)
    except AssertionError:
        print('Failed to get gurued vocabulary', file=stderr)
        return None
    gurued_ids = [item['data']['subject_id'] for item in gurued_data]
    return [item['data']['characters'] for item in wk_data if item['id'] in gurued_ids]
    
def get_wk_data_from_url(url: str, headers: dict) -> list[dict]:
    
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        raise AssertionError(f'Failed to get {url}, got code {req.status_code}')
    data = req.json()['data']
    if 'pages' in req.json():
        next_url = req.json()['pages']['next_url']
        while True:
            req = requests.get(next_url, headers=headers)
            if req.status_code != 200:
                raise AssertionError(f'Failed to get {next_url}, got code {req.status_code}')
            data = data + req.json()['data']
            next_url = req.json()['pages']['next_url']
            if next_url is None:
                break
        return data
    else:
        return [data]
