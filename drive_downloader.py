import requests

def download_drive_item(id, destination):
    '''Downloads the file with the given id
    '''
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32768

        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    try:
        response = session.get(URL, params = { 'id' : id }, stream = True)
        token = get_confirm_token(response)

        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)

        print(response.url)
        print(str(response.status_code))
        print(response.headers)
        if response.status_code != 200:
            print("Failed to download item with ID: " + str(id))
            return -1
        save_response_content(response, destination)
        return 1
    except:
        
        print("Drive Download Error")
        return -1