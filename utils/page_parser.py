import re
from bs4 import BeautifulSoup


def extract_canvas_file_links(html_content):
    """Extract Canvas file download links from HTML content."""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    file_links = []
    
    # Look for Canvas file holder structures first
    file_holders = soup.find_all('span', class_='instructure_file_holder')
    for holder in file_holders:
        link = holder.find('a', href=True)
        if link:
            href = link['href']
            file_id_match = re.search(r'/files/(\d+)', href)
            if file_id_match:
                file_links.append({'file_id': file_id_match.group(1)})
    
    # Also find regular links to files (fallback)
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Skip if we already found this in a file holder
        if any(fl['url'] in href or href in fl['url'] for fl in file_links):
            continue
        
        # Look for Canvas file links (various patterns)
        patterns = [
            r'/courses/\d+/files/\d+',           # Direct file links
            r'/files/\d+',                       # Short file links  
            r'/courses/\d+/files/\d+/download',  # Download links
            r'/files/\d+/download'               # Short download links
        ]
        
        for pattern in patterns:
            if re.search(pattern, href):
                file_id_match = re.search(r'/files/(\d+)', href)
                file_links.append({'file_id': file_id_match.group(1) if file_id_match else None})
                break
    
    return file_links