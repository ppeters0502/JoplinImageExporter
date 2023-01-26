import requests
import sys
import os
import re
from os.path import exists
from base64 import b64encode
from dotenv import load_dotenv

load_dotenv()
API_URL = 'https://api.imgur.com'
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
# Token is valid for one month
# To request a new token, open a browser and go to https://api.imgur.com/oauth2/authorize?response_type=token&client_id=<CLIENT_ID>
# On the authorize page, check storage in the dev tools, copy the token that's there, and then click the "agree" button and you should be good to go
auth_token = os.getenv('AUTH_TOKEN')
refresh_token = os.getenv('REFRESH_TOKEN')

'''
Total Steps needed:
1. Grab path passed in, and check if path is a joplin file
2. Scrape Joplin file to find all image markdowns
3. Grab image paths in the markdown to find the image
4. Upload Image to Imgur
5. Take image URL in the response and apply it in Joplin
'''


def getImgurAuthToken():
    """
    In the event that the auth token is expired, this function requests a new token.
    """
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post(f'{API_URL}/oauth2/token', data=data).json()
    if (response['access_token']):
        print(f'New Access Token: {response["access_token"]}')
        print(f'New Refresh Token: {response["refresh_token"]}')


def print_help():
    """
    Print help and usage message.
    """

    print('\njoplinUploadImages.py')
    print('=================================================================')
    print('Purpose: Scrapes MD file exported from Joplin, \nfinds all images in the MD file, \nand uploads those images to a given Imgur account.') 
    print('''\nTool then updates the MD file to replace all of the attached images \n with image links to the uploaded Imgur versions, so that you don't need any referenced \n"resources" folder.''')
    print('USAGE: python joplinUploadImages.py <VALID MARKDOWN FILE PATH>')
    print('To get new Imgur authorization tokens: python joplinUploadImages.py -n')
    print('REQUIREMENTS: Imgur API token that you get from providing a ClientID to. More info here: \n https://apidocs.imgur.com/')


def uploadToImgur(alt: str, filePath: str) -> str:
    filePath = filePath.replace('(', '').replace(')', '')
    if (exists(filePath)):
        headers = {
            "Authorization": f"Bearer {auth_token}"
        }
        response = requests.post(f'{API_URL}/3/image', headers=headers, data={
            'image': b64encode(open(filePath, 'rb').read()),
        }).json()
        if (response['success'] and response['data']['link']):
            link = response['data']['link']
            return link
        else:
            print('Request Not Successful')
            return None
    else:
        print('File does not exist')
        return None

def updateFile(fileString: str):
    print(f'Scraping Joplin file {fileString}')
    replacedLines = []
    with open(fileString, 'r') as file:
        data = file.readlines()
        for line in data:
            imgRegex = re.compile(r'(!\[.+\])(\(.+\))')
            searchObj = imgRegex.search(line)
            if (searchObj):
                alt, url = searchObj.groups()
                print(f'alt: {alt} - url: {url}')
                rename = uploadToImgur(alt, url)
                if (rename):
                    replaced = f'{alt}({rename})'
                else:
                    replaced = line
            else:
                replaced = line
            replacedLines.append(replaced)

    with open(fileString, 'w') as writingFile:
        for line in replacedLines:
            writingFile.write(line)

def main():
    try:
        path = sys.argv[1]
    except IndexError:
        print('[!] Error - Invalid Arguments')
        print_help()
        exit(1)
    if (path =='-n'):
        getImgurAuthToken()
        exit(0)
    
    if (os.path.exists(path) == False):
        print('[!] Error - Path does not exist')
        print_help()
        exit(1)
    isDirCommand = False
    if (os.path.isdir(path)):
        isDirCommand = True
        os.chdir(path)
    elif (os.path.isfile(path)):
        os.chdir(os.path.dirname(path))
    
    print(os.getcwd())
    if isDirCommand:
        for markdownFile in os.listdir(os.getcwd()):
            if markdownFile.endswith(".md"):
                updateFile(os.path.join(f'{os.getcwd()}\\{markdownFile}'))
    else:
        updateFile(path)
    

if __name__ == "__main__":
    main()
