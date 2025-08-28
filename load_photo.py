import os
from dotenv import load_dotenv
from pathlib import Path
from lib.y360_api.api_script import API360
from PIL import Image

def main_menu():

    dry_run = False
    if os.environ.get('DRY_RUN').lower() == "true":
        dry_run = True
    
    if os.environ.get('RESIZE_IMAGE').lower() == "false":
        is_resize = False
    elif os.environ.get('RESIZE_IMAGE').lower() == "true":
        is_resize = True
    else:
        print("Unknown value for RESIZE_IMAGE in config. Exit.")
        return
    
    if is_resize:
        resize_width = int(os.environ.get('RESIZE_WIDTH'))
        if resize_width <= 0:
            print("RESIZE_WIDTH must be greater than 0. Exit.")
            return
        elif resize_width > 1000:
            print("RESIZE_WIDTH must be less than 1000. Exit.")
            return
    
    dir_path = Path(os.environ.get('PHOTO_DIR'))
    if not dir_path.exists:
        print(f"The path '{dir_path}' does not exist. Check path and letter case. Exit.")
        return
    if not dir_path.is_dir():
        print(f"The path '{dir_path}' is not a directory. Exit.")
        return

    print("Reading users from Y360 catoalog...")
    users = organization.get_all_users(False)
    if not users:
        print("There are no users in Y360 catalog. Exit.")
        return
    else:
        print(f"Got {len(users)} users from Y360 catalog")

    if os.environ.get('IMAGE_EXT').lower() == "jpg":
        files = list(dir_path.glob('*.jpg'))
    elif os.environ.get('IMAGE_EXT').lower() == "png":
        files = list(dir_path.glob('*.png'))
    else:
        print(f"Unknown image extension in config - {os.environ.get('IMAGE_EXT')}. Exit.")
        return
    
    if not files:
        print(f"There are no files with extension {os.environ.get('IMAGE_EXT').lower()} in directory {dir_path}. Check case of extension, must be jpg or png. Exit.")
        return
    else:
        print(f"Got {len(files)} files with extension {os.environ.get('IMAGE_EXT').lower()} in directory {dir_path}.")

    print("Loading photos to Y360 catalog...")
    
    for file_path in files:
        name = file_path.stem.lower()
        for user in users:
            if user["nickname"].lower() == name or name in user["aliases"]:
                print(f"Loading photo for user {user['nickname']} (file - {file_path})")
                if dry_run:
                    print(f"Dry run. Skipping photo loading for user {user['nickname']} (file - {file_path})")
                else:
                    if is_resize:
                        resize_image(file_path)
                        full_path = file_path.with_stem(f"{file_path.stem}_resized")
                    else:
                        full_path = file_path
                    organization.load_photo(user["id"], full_path, name)
                break


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


if __name__ == "__main__":
    denv_path = os.path.join(os.path.dirname(__file__), '.env')

    if os.path.exists(denv_path):
        load_dotenv(dotenv_path=denv_path,verbose=True, override=True)
    
    organization = API360(os.environ.get('orgId'), os.environ.get('access_token'))
    
    main_menu()
