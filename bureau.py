import requests

def cpf_bureau_check(cpf: str) -> dict:
    url = "https://api.serasa.com/check"
    payload = {"cpf": cpf}
    headers = {"Authorization": "Bearer ACESS_TOKEN"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}