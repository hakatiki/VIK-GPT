import os 
import gdown

# os.mkdir('faiss_db2')


def download_google_drive_folder(folder_id):
    # Construct the URL to the folder
    url = f'https://drive.google.com/drive/folders/{folder_id}'

    # Use gdown to download the folder
    gdown.download_folder(url, quiet=False, use_cookies=False)

# The folder ID for your Google Drive folder
folder_id = '1-4HxQ0Qmp9dmBrdY2klDHzj7RorTWy1b'

# Call the function to download the folder
download_google_drive_folder(folder_id)
