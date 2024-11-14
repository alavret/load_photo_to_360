import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from lib.y360_api.api_script import API360
from PIL import Image

def main_menu():

    users = organization.get_all_users(False)
    nicknames = {}
    for u in users:
        nicknames[u["nickname"]] = u["id"]
    dir_path = os.environ.get('PHOTO_DIR')
    for k,v in nicknames.items():
        full_path = dir_path + k + "." + os.environ.get('IMAGE_EXT')
        if os.path.exists(full_path):
             if os.environ.get('RESIZE_IMAGE'):
                resize_image(dir_path, k)
                full_path = dir_path + k + "_resized." + os.environ.get('IMAGE_EXT').lower()
             organization.load_photo(v, full_path, k)
        else:
            print(f"Photo for {k} not exist.")

def resize_image(dir_path, nickname):
    base_width = int(os.environ.get('RESIZE_WIDTH'))
    img = Image.open(dir_path + nickname + "." + os.environ.get('IMAGE_EXT'))
    wpercent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    full_path = dir_path + nickname + "_resized." + os.environ.get('IMAGE_EXT').lower()
    save_format = "PNG"
    if os.environ.get('IMAGE_EXT').upper() == "JPG":
        save_format = "JPEG"
    img.save(full_path, save_format)


if __name__ == "__main__":
    denv_path = os.path.join(os.path.dirname(__file__), '.env')

    if os.path.exists(denv_path):
        load_dotenv(dotenv_path=denv_path,verbose=True, override=True)
    
    organization = API360(os.environ.get('orgId'), os.environ.get('access_token'))
    
    main_menu()
