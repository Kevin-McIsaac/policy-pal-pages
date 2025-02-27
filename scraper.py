import os
import re
import requests
from urllib.parse import urlparse, urljoin
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

    def remove_script(self, html: str) -> str:
        '''Remove script elements that cause session expired messages'''
        soup = BeautifulSoup(html, 'html.parser')
        for element in soup("script"):
            element.decompose()

        return str(soup)

    def save_content(self, url, html_content):
        '''Save html_content to file path in url'''

        path, _ = self.get_path(url)
        full_path =  self.download_path + path
        directory = os.path.dirname(full_path)        
        if not os.path.exists(directory):
            os.makedirs(directory) 

        logger.info(f"Downloading {url} to {full_path}")
        with open(full_path, 'w') as f:
            f.write(html_content)

        self.download.add(url)

    def save_url(self, url:str, starting_page) -> str:
        '''Save the content at url to the download path in url'''

        html_content = self.fetch_content(url)
        html_content = self.remove_script(html_content)

        if not(starting_page or self.search_only):
            self.save_content(url, html_content)
            
        return html_content
    
    def aspx_link_to_html_link(self, aspx_url) -> None:
        '''Extract the html links from the aspx file'''
        
        aspx_content = self.fetch_content(aspx_url)
        
        # Links in dynamic content function
        pattern = r'LoadDynamicContent\(([^,)]+),([^,)]+),([^,)]+)\)'
        matches = re.findall(pattern, aspx_content)
        
        if len(matches) > 0 :
            # return  [urljoin(arg1,arg2) for arg1, arg2, _ in matches]
            html_urls =  [(arg1 + arg2).replace('"', '').replace(' ', '') for arg1, arg2, _ in matches]
        else:
        # or links in an input tag
            pattern = r'<input[^>]*value="([^"]*\.html)"[^>]*>'
            html_urls = re.findall(pattern, aspx_content, re.DOTALL)
        
        if len(html_urls) == 0:
            logger.warning(f"No urls in apsx {aspx_url}")
            return None
        elif len(html_urls) > 1:
            logger.warning(f"Too many urls in aspx {aspx_url}: {html_urls}")
        
        return html_urls[0]
        
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
    
    def skip(self, url:str, depth:int, exclude:list[str]) -> bool:  
        """Check if the URL should be skipped"""

        # Stop if depth is exceeded. Check before caching incase
        # this url show up later in a higher layer. 
        if depth and depth <= 0:
            logger.info(f"Bottomed out at {depth} {url}")
            self.bottomed_out.add(url)
            return True

        path, extension = self.get_path(url)
        if path in self.cache:
            return True
        
        self.cache.add(path)
    
        if not url.startswith(self.domain):
            logger.info(f"Skipping domain {url}")
            return True

        # Skip unwanted videos etc
        if extension not in [".html", ".aspx", ""]:
            logger.info(f"Skipping unwanted extention {extension} in {url}")
            return True
        
        # Skip unwanted URLs
        for exclude_url in exclude:
            if exclude_url in url:
                logger.info(f"Skipping excluded {exclude_url}")
                return True
        


        return False
    
    def get_path(self, url:str) -> str:
        path = urlparse(url).path
        extension = os.path.splitext(path)[-1].lower()
        if extension == "":
            extension = ".html"   
            path += ".html"    
        
        return path, extension
        
    def extract(self, html_content:str, depth:int, element:str) -> None:
        soup = BeautifulSoup(html_content, features="html.parser")
        for link in soup.select(f'{element} a'):     
            if href := link.get('href'):
                # logger.info(href)
                url_parsed = urlparse(href)
                if url_parsed.scheme in ['https', 'http', ''] and url_parsed.path != "" :                  
                    if url_parsed.scheme == "":
                        href = urljoin(self.domain, href)
                
                    self.scrape(href, depth=depth-1, starting_page=False)