import gdown
url = 'https://drive.google.com/drive/folders/1is609sosAdqf9YJAfwr72hBqM4OeNuZq?usp=sharing'
gdown.download_folder(url, quiet=False, use_cookies=False, output='/opt/vpn_detection/datasets/raw/ISCX-VPN')
