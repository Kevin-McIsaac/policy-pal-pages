import requests

def login_with_cookies(url_login, username, password, url_protected):
    """Logs in to a website and accesses a protected resource."""

    session = requests.Session()

    # Login request
    login_data = {
        'username': username,
        'password': password,
        'request_id': ""
    }
    response_login = session.post(url_login, data=login_data)

    # Check if login was successful
    if response_login.status_code == 200: #or other successful status code.
        print("Login successful!")

        # Access protected resource
        response_protected = session.get(url_protected)

        # Process the protected resource's content
        print(response_protected.text)

    else:
        print(f"Login failed. Status code: {response_login.status_code}")

#Example usage. Replace with your target website's urls, and login credentials.
url_login = 'https://brokerportal.suncorpbank.com.au/oam/server/auth_cred_submit'
url_protected = 'https://brokerportal.suncorpbank.com.au/home.html'
username = "EU4796441"
password = "Maximilian1!"

login_with_cookies(url_login, username, password, url_protected)