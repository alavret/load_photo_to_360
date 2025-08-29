import os
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
import requests
from http import HTTPStatus
import time

DEFAULT_360_API_URL = "https://api360.yandex.net"
ITEMS_PER_PAGE = 100
MAX_RETRIES = 3
RETRIES_DELAY_SEC = 2

def main_menu():

    dry_run = False

    oauth_token = os.environ.get("access_token")
    orgId = os.environ.get("orgId")
    if oauth_token is None:
        print("!!! ERROR !!! OAuth token is not set. Exit.")
        return
    if orgId is None:
        print("!!! ERROR !!! Organization ID is not set. Exit.")
        return
    
    if not check_oauth_token(oauth_token, orgId):
        print("!!! ERROR !!! OAuth token or OrgId are not valid. Exit.")
        return

    if os.environ.get('DRY_RUN').lower() == "true":
        dry_run = True
    
    if os.environ.get('RESIZE_IMAGE').lower() == "false":
        is_resize = False
    elif os.environ.get('RESIZE_IMAGE').lower() == "true":
        is_resize = True
    else:
        print("!!! ERROR !!! Unknown value for RESIZE_IMAGE in config. Exit.")
        return
    
    if is_resize:
        resize_width = int(os.environ.get('RESIZE_WIDTH'))
        if resize_width <= 0:
            print("!!! ERROR !!! RESIZE_WIDTH must be greater than 0. Exit.")
            return
        elif resize_width > 1000:
            print("!!! ERROR !!! RESIZE_WIDTH must be less than 1000. Exit.")
            return
    
    dir_path = Path(os.environ.get('PHOTO_DIR'))
    if not dir_path.exists:
        print(f"!!! ERROR !!! The path '{dir_path}' does not exist. Check path and letter case. Exit.")
        return
    if not dir_path.is_dir():
        print(f"!!! ERROR !!! The path '{dir_path}' is not a directory. Exit.")
        return

    #print("Reading users from Y360 catoalog...")
    users = get_all_api360_users_from_api(oauth_token, orgId)
    if not users:
        print("!!! ERROR !!! There are no users in Y360 catalog. Exit.")
        return
    else:
        print(f"Got {len(users)} users from Y360 catalog")

    if os.environ.get('IMAGE_EXT').lower() == "jpg":
        files = list(dir_path.glob('*.jpg'))
    elif os.environ.get('IMAGE_EXT').lower() == "png":
        files = list(dir_path.glob('*.png'))
    else:
        print(f"!!! ERROR !!! Unknown image extension in config - {os.environ.get('IMAGE_EXT')}. Exit.")
        return
    
    if not files:
        print(f"!!! ERROR !!! There are no files with extension {os.environ.get('IMAGE_EXT').lower()} in directory {dir_path}. Check case of extension, must be jpg or png. Exit.")
        return
    else:
        print(f"Got {len(files)} files with extension {os.environ.get('IMAGE_EXT').lower()} in directory {dir_path}.")

    print("Loading photos to Y360 catalog...")
    
    
    for file_path in files:
        name = file_path.stem.lower()
        is_found = False
        for user in users:
            if user["nickname"].lower() == name or name in user["aliases"]:
                print(f"Loading photo for user {user['nickname']} (file - {file_path})")
                is_found = True
                if dry_run:
                    print(f"Dry run. Skipping photo loading for user {user['nickname']} (file - {file_path})")
                else:
                    if is_resize:
                        resize_image(file_path)
                        full_path = file_path.with_stem(f"{file_path.stem}_resized")
                    else:
                        full_path = file_path
                    
                    if load_photo(user["id"], full_path, orgId, oauth_token):
                        print(f"Photo loaded for user {user['nickname']} (file - {file_path})")
                    else:
                        print(f"!!! ERROR !!! Photo loading for user {user['nickname']} (file - {file_path}) failed.") 
                break
        if not is_found:
            if not file_path.stem.lower().endswith("_resized"):
                print(f"!!! Warning !!! User with name _ {name} _ not found in Y360 catalog. Skipping photo loading for user {name} (file - {file_path})")

def resize_image(file_path):
    base_width = int(os.environ.get('RESIZE_WIDTH'))
    img = Image.open(file_path)
    wpercent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    full_path = file_path.with_stem(f"{file_path.stem}_resized")
    save_format = "PNG"
    if os.environ.get('IMAGE_EXT').upper() == "JPG":
        save_format = "JPEG"
    img.save(full_path, save_format)

def check_oauth_token(oauth_token, org_id):
    """Проверяет, что токен OAuth действителен."""
    url = f"{DEFAULT_360_API_URL}/directory/v1/org/{org_id}/users?perPage=100"
    headers = {
        "Authorization": f"OAuth {oauth_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == HTTPStatus.OK:
        return True
    return False

def http_get_request(url, headers):
    try:
        retries = 1
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code != HTTPStatus.OK.value:
                print(f"!!! ERROR !!! during GET request url - {url}: {response.status_code}. Error message: {response.text}")
                if retries < MAX_RETRIES:
                    print(f"Retrying ({retries+1}/{MAX_RETRIES})")
                    time.sleep(RETRIES_DELAY_SEC * retries)
                    retries += 1
                else:
                    print(f"!!! Error !!! during GET request url - {url}.")
                    break
            else:
                break

    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR !!! {type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

    return response

def get_all_api360_users_from_api(oauth_token, org_id):
    print("Getting all users of the organisation...")
    url = f"{DEFAULT_360_API_URL}/directory/v1/org/{org_id}/users?perPage=100"
    headers = {"Authorization": f"OAuth {oauth_token}"}
    has_errors = False
    response = http_get_request(url, headers=headers)
    if response.status_code == HTTPStatus.OK.value:
        users = response.json()['users']
        for i in range(2, response.json()["pages"] + 1):
            print(f"Getting users from API, page {i} of {response.json()['pages']} (one page = 100 users)")
            response = http_get_request(f"{url}&page={i}", headers=headers)
            if response.status_code == HTTPStatus.OK.value:
                users.extend(response.json()['users'])
            else:
                has_errors = True
                break
    else:
        has_errors = True

    if has_errors:
        print("!!! Error !!! during GET request. Return empty list.")
        return []
    
    return users

def load_photo(userId, full_path, orgId, oauth_token):
    file_name, file_extension = os.path.splitext(full_path)
    photo_headers = {
        "Authorization": f"OAuth {oauth_token}",
        "Content-Type": f"image/{file_extension.lower()}"
    }
    url = f"{DEFAULT_360_API_URL}/directory/v1/org/{orgId}/users/{userId}/avatar"
    response = None
    try:
        retries = 1
        while True:
            response = requests.put(url, data=open(full_path,'rb'), headers=photo_headers)
            if response.status_code != HTTPStatus.OK.value:
                print(f"!!! ERROR !!! during PUT request url - {url}: {response.status_code}. Error message: {response.text}")
                if retries < MAX_RETRIES:
                    print(f"Retrying ({retries+1}/{MAX_RETRIES})")
                    time.sleep(RETRIES_DELAY_SEC * retries)
                    retries += 1
                else:
                    print(f"!!! Error !!! during PUT request url - {url}.")
                    break
            else:
                break

    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR !!! {type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

    if response:
        if response.status_code == HTTPStatus.OK.value:
            return True
        
    return False
    response = requests.put(url, data=open(full_path,'rb'), headers=photo_headers)
    if response.status_code == 200:
        return True
        print(f"Photo for User {nickname} was uploaded successfully")
    else:
        print(f"During creating user {nickname} occurred error: {response.reason}")


if __name__ == "__main__":
    denv_path = os.path.join(os.path.dirname(__file__), '.env')

    if os.path.exists(denv_path):
        load_dotenv(dotenv_path=denv_path,verbose=True, override=True)
    
    main_menu()
