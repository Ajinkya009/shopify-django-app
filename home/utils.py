import requests

def schedule_call(phone:str,encoded_params:str) -> None:
    url:str = "https://teamone.awaaz.de/collections/shopify/" + phone + "/schedule_call"
    response = requests.post(url, data=encoded_params)
    print(response)
    return