import requests

BASE_URL = 'https://www.itdashboard.gov/data-feeds'
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.itdashboard.gov',
    'Referer': 'https://www.itdashboard.gov/data-feeds',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
}

def fetch_and_save_data(domain_value, filename):
    data = {
        'domain': 'it_portfolio',
        'it_portfolio': domain_value,
        'data_center': '',
        'web_metric': '',
        'agency_dummy': '000',
        'op': 'CSV',
        'form_id': 'data_feeds_form',
    }

    response = requests.post(BASE_URL, headers=HEADERS, data=data)


    if response.status_code == 200:
        try:
            with open(filename, 'w') as f:
                f.write(response.text)
                # print(f"{filename} saved successfully!")
                return f"{filename} saved successfully"
        except:
             return f"Failed to fetch data for {filename}"
    else:
        return f"Failed to fetch data for {filename}. Status code: {response.status_code}"

def funding_sources():
    try:
        return fetch_and_save_data('it_portfolio_funding_sources', 'app/files/funding_sources.csv')
    except:
        return "funding sources.csv scraping failed"
    

def projects():
    
    try:
        return fetch_and_save_data('projects', 'app/files/projects.csv')
    except:
        return "projects.csv scraping failed"

# if __name__ == '__main__':
#     funding_sources()
#     projects()
