import os
import re
import requests
from urllib.parse import urlparse
from loguru import logger
from bs4 import BeautifulSoup

class WebScraper():
    def __init__(self, domain:str, cookie:str, download_path:str, class_names):

        self.cookie = cookie   
        self.download_path = download_path
        self.class_names = class_names
        self.cache = set()
        self.download = set()
        self.bottomed_out = set()
        self.domain = domain
        self.session = requests.Session()

    def fetch_content(self, url:str) -> str:
        ''' Get the contents of a URL using a logged in cookie'''

        try:
            response = self.session.get(url, cookies={'Cookie': self.cookie})
        
            if not response:
                logger.warning(f"No response for {url}")
                return ""
            if response.status_code != 200:
                logger.warning(f"Response {response.status} for {url}")
                return ""
        
            return response.text
        
        except Exception as e:
            logger.error(f"Error {repr(e)} for {url}")
            return ""
      
    def save_url(self, url:str) -> str:
        '''Save the url to the download path and return the contents'''
        html_content = self.fetch_content(url)

        full_path =  self.download_path + urlparse(url).path
        directory = os.path.dirname(full_path)
        
        if not os.path.exists(directory):
            os.makedirs(directory) 

        logger.info(f"Downloading {url}")
        with open(full_path, 'w') as f:
            f.write(html_content)

        self.download.add(url)

        return html_content

    def aspx_link_to_html_link(self, aspx_url) -> list[str]:
        '''Extract the html links from the aspx file'''
        
        aspx_content = self.fetch_content(aspx_url)

        # Links in dynamic content function
        pattern = r'LoadDynamicContent\(([^,)]+),([^,)]+),([^,)]+)\)'
        matches = re.findall(pattern, aspx_content)
        if len(matches) >0 :
            # return  [urljoin(arg1,arg2) for arg1, arg2, _ in matches]
            return  [(arg1 + arg2).replace('"', '').replace(' ', '') for arg1, arg2, _ in matches]
        
        # or links in an input tag
        pattern = r'<input[^>]*value="([^"]*\.html)"[^>]*>'
        matches = re.findall(pattern, aspx_content, re.DOTALL)
        if matches:
            return matches
        
        logger.warning(f"{aspx_url} no html URL")
        return []
        
    def fetch_html_links(self, html_page) -> list[str]:
        '''Find all the links in the page'''
        soup = BeautifulSoup(html_page)

        links = []
        for class_name in self.class_names:
            for link in soup.select('div#wrapper a'):
                        if href := link.get('href'):
                            if href.startswith("/Net/Documentum/"):
                                href = self.domain+href
                            if not href.endswith('.aspx'):
                                print("Not an ASPX", href)
                            links.append(href) 
        return links
    
    def skip(self, url:str, depth:int):
        """Check if the URL should be skipped"""

        path = urlparse(url).path
        if path in self.cache:
            return True
        
        self.cache.add(path)
    
        if not url.startswith(self.domain):
            logger.info(f"Skipping domain {url}")
            return True

        # Skip unwanted videos etc
        extension = os.path.splitext(path)[-1].lower()
        if extension not in [".html", ".aspx"]:
            logger.info(f"Skipping unwanted extention  {url}")
            return True
        
        if "Logon.aspx" in path:
            return True
        
        # Stop if depth is exceeded
        if depth and depth <= 0:
            logger.info(f"Bottomed out at {depth} {url}")
            self.bottomed_out.add(url)
            return True

        return False