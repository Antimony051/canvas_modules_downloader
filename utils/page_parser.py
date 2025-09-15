import re
from bs4 import BeautifulSoup


def extract_canvas_file_links(html_content, canvas_base_url):
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
            filename = link.get_text(strip=True)
            
            # Look for file ID in href or data attributes
            file_id_match = re.search(r'/files/(\d+)', href)
            if file_id_match:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = canvas_base_url.rstrip('/') + href
                else:
                    full_url = href
                
                file_links.append({
                    'url': full_url,
                    'filename': filename,
                    'file_id': file_id_match.group(1)
                })
    
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
            file_match = re.search(pattern, href)
            if file_match:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = canvas_base_url.rstrip('/') + href
                else:
                    full_url = href
                
                # Extract filename from link text or href
                filename = link.get_text(strip=True)
                if not filename or len(filename) > 100:  # Use href-based name if text is too long/empty
                    filename = href.split('/')[-1] or 'file'
                
                # Extract file ID
                file_id_match = re.search(r'/files/(\d+)', href)
                file_id = file_id_match.group(1) if file_id_match else None
                
                file_links.append({
                    'url': full_url,
                    'filename': filename,
                    'file_id': file_id
                })
                break
    
    return file_links