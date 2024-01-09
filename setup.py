import os 
import gdown


def download_google_drive_folder(folder_id):
    url = f'https://drive.google.com/drive/folders/{folder_id}'
    gdown.download_folder(url, quiet=False, use_cookies=False)

folder_id = '1-4HxQ0Qmp9dmBrdY2klDHzj7RorTWy1b'
download_google_drive_folder(folder_id)