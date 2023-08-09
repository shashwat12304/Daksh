from flask import Flask, request, jsonify
import tensorflow as tf
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import tensorflow as tf
import requests
import re

app = Flask(__name__)

loaded_model = tf.keras.models.load_model(r'model_weights_v2.h5')


def detect_missing_title(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        title_tag = soup.find('title')

        if title_tag is None:
            return 1  # Missing title
        elif not title_tag.string.strip():
            return 1  # Empty title
        else:
            return 0  # Title present and not empty
    else:
        return -1 
    
def detect_iframe_or_frame(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        iframe_elements = soup.find_all('iframe')
        frame_elements = soup.find_all('frame')

        iframes_count = len(iframe_elements)
        frames_count = len(frame_elements)
        
        if iframes_count or frames_count:
            return 1
        else:
            return 0
    else:
        return -1
    
def detect_submit_info_to_email(url): #changed
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        forms_with_email_input = []

        for form in soup.find_all('form'):
            email_input = form.find('input', attrs={'type': 'email'})
            submit_button = form.find('input', attrs={'type': 'submit'})

            if email_input is not None and submit_button is not None:
                forms_with_email_input.append(form)
        if not forms_with_email_input:
            return 0
        else: 
            return 1
    else:
        return -1
    
def detect_popup_window(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        popup_elements = soup.find_all('script', string=re.compile(r'window\.open'))
        
        if popup_elements:
            return 1  # Popup window detected
        else:
            return 0  # No popup window detected
    else:
        return -1  # Unable to fetch URL
    
def detect_fake_link_in_status_bar(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        fake_links = []

        for a_tag in soup.find_all('a', href=True):
            actual_href = a_tag['href']
            displayed_text = a_tag.get_text().strip()

            if displayed_text:
                # Remove any spaces or non-breaking spaces from the displayed text
                displayed_text = re.sub(r'\s|&nbsp;', '', displayed_text)
                
                if actual_href and actual_href != displayed_text:
                    fake_links.append({
                        'displayed_text': displayed_text,
                        'actual_href': actual_href
                    })
        if not fake_links:
            return 0
        else: 
            return 1
    else:
        return -1    
    
def detect_abnormal_form_action(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        abnormal_forms = []

        for form_tag in soup.find_all('form', action=True):
            action_url = form_tag['action']
            
            # Check if the action URL is different from the original URL's domain
            if action_url and not action_url.startswith('/') and not action_url.startswith(url):
                abnormal_forms.append({
                    'form_action': action_url
                })
        if not abnormal_forms:
            return 0
        else: 
            return 1
    else:
        return -1  
    
def detect_pct_null_self_redirect_hyperlinks(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        total_hyperlinks = 0
        null_self_redirect_hyperlinks = 0

        for a_tag in soup.find_all('a', href=True):
            total_hyperlinks += 1
            href = a_tag['href']
            
            # Compare the href attribute to the URL to check for null self-redirects
            if href == url or href == url + '/':
                null_self_redirect_hyperlinks += 1
        
        # Calculate the percentage of null self-redirect hyperlinks
        if total_hyperlinks > 0:
            pct_null_self_redirect_hyperlinks = (null_self_redirect_hyperlinks / total_hyperlinks) 
        else:
            pct_null_self_redirect_hyperlinks = 0
        
        return pct_null_self_redirect_hyperlinks
    else:
        return -1
    
def detect_right_click_disabled(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text

        # Check if right-click is disabled in the HTML content
        right_click_disabled = re.search(r'oncontextmenu\s*=\s*["\']return\s*false["\']', html_content, re.I)
        
        if right_click_disabled:
            return 1  # Right-click is disabled
        else:
            return 0  # Right-click is not disabled
    else:
        return 0
    

def has_relative_form_action(parsed_url):
    try:
        # Fetch the HTML content of the URL
        response = requests.get(parsed_url.geturl())
        response.raise_for_status()

        # Parse HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all form elements
        form_elements = soup.find_all('form')

        # Check each form for relative form actions
        for form in form_elements:
            action = form.get('action', '').lower()
            if not action.startswith(('http://', 'https://')):
                return 1  # Relative form action found

        return 0  # No relative form actions found

    except requests.exceptions.RequestException:
        return -1

def has_insecure_forms(parsed_url):
    try:
        # Fetch the HTML content of the URL
        response = requests.get(parsed_url.geturl())
        response.raise_for_status()

        # Parse HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all form elements
        form_elements = soup.find_all('form')

        # Check each form for insecure attributes like 'http' in action attribute
        for form in form_elements:
            action = form.get('action', '').lower()
            if 'http://' in action or 'https://' not in action:
                return 1  # Insecure form found

        return 0  # No insecure forms found

    except requests.exceptions.RequestException:
        return -1 

def has_external_favicon(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all link elements with rel="icon" or rel="shortcut icon"
        favicon_links = soup.find_all('link', rel=re.compile(r'^icon$', re.I))
        
        for link in favicon_links:
            href = link.get('href')
            # Check if the favicon URL is external (not relative)
            if href and not href.startswith(('http://', 'https://')):
                return 1
        
        return 0
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return -1

def calculate_external_resource_percentage(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        total_resources = 0
        external_resources = 0

        for tag in ['img', 'link', 'script', 'iframe', 'source']:
            for resource in soup.find_all(tag):
                resource_url = resource.get('src') or resource.get('href')
                if resource_url:
                    total_resources += 1
                    parsed_url = urlparse(resource_url)
                    if parsed_url.netloc != urlparse(url).netloc:
                        external_resources += 1

        if total_resources > 0:
            external_percentage = (external_resources / total_resources)
            return external_percentage
        else:
            return 0
    else:
        print(f"Failed to fetch the URL: {response.status_code}")
        return -1

def get_external_links_percentage(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        external_count = 0
        total_count = 0
        
        # Get the base domain of the URL
        base_domain = urlparse(url).netloc
        
        # Find all <a> tags in the HTML
        for a_tag in soup.find_all('a'):
            total_count += 1
            href = a_tag.get('href')
            if href:
                parsed_href = urlparse(href)
                # Check if the link is not empty and has a netloc (domain)
                if parsed_href.netloc and parsed_href.netloc != base_domain:
                    external_count += 1
        
        if total_count == 0:
            return 0.0
        else:
            percentage = (external_count / total_count) 
            return percentage
    else:
        print("Failed to fetch the URL.")
        return -1

def extract_embedded_brand_name(url):
    brand_keywords = ["Apple", "Amazon", "Google", "Microsoft", "Coca-Cola", "Samsung", "Toyota", "Mercedes-Benz", "McDonald's", "Nike", "Adidas", "Facebook", "Disney", "Walmart", "Tesla", "Starbucks", "Louis Vuitton", "Chanel", "Gucci", "Hermès", "Honda", "BMW", "Visa", "Mastercard", "Airbnb", "Uber", "Lyft", "Slack", "Airtable", "Figma", "Canva", "Grammarly", "Evernote", "Trello", "Asana", "Dropbox", "Squarespace", "Shopify", "Mailchimp", "Stripe", "Zoom", "Peloton", "Casper", "Away", "Cotopaxi", "Allbirds", "Warby Parker", "Everlane", "Glossier", "ThredUp", "Rent the Runway", "HelloFresh", "Dollar Shave Club", "Harry's", "BarkBox", "Stitch Fix", "Bombas", "Allswell", "Quip", "MeUndies", "Native", "ThirdLove", "Outdoor Voices", "Untuckit", "Bonobos", "Rothy's", "Brooklinen", "Leesa", "Winky Lux", "Milk Makeup", "The Ordinary", "Sunday Riley", "Drunk Elephant", "Fenty Beauty", "ColourPop", "Thrive Causemetics", "Tula", "Sunday General", "Mejuri", "Hims", "Hers", "Billie", "Mirror", "Tempo", "Gymshark", "Lululemon", "Athleta", "Reformation", "Girlfriend Collective", "Cuyana", "Oatly", "Birdies", "Native Shoes", "ADAY", "Mack Weldon"]
    
    for keyword in brand_keywords:
        if re.search(r'\b' + keyword + r'\b', url, re.IGNORECASE):
            return keyword
    
    return 0

def extract_url_features(url):
    parsed_url = urlparse(url)
    random_string_pattern = r"[A-Za-z0-9]{10,}"
    
    NumDots = url.count('.')
    SubdomainLevel = url.count('.') - 1
    PathLevel = url.count('/')
    UrlLength = len(url)
    NumDash = url.count('-')
    NumDashInHostname = parsed_url.netloc.count('-')
    AtSymbol = 1 if '@' in url else 0
    TildeSymbol = 1 if '~' in url else 0
    NumUnderscore = url.count('_')
    NumPercent = url.count('%')
    NumQueryComponents = len(parsed_url.query.split('&'))
    NumAmpersand = url.count('&')
    NumHash = url.count('#')
    NumNumericChars = sum(c.isdigit() for c in url)
    NoHttps = 1 if not url.startswith('https://') else 0
    
    RandomString = 0  # Replace this with the actual method to determine if there's a random string in the URL
    
    IpAddress = 1 if parsed_url.netloc.replace('.', '').isdigit() else 0
    DomainInSubdomains = 1 if parsed_url.netloc.count('.') > 1 else 0
    DomainInPaths = 1 if '/' + parsed_url.netloc.replace('.', '/') in parsed_url.path else 0
    HttpsInHostname = 1 if 'https' in parsed_url.netloc else 0
    HostnameLength = len(parsed_url.netloc)
    PathLength = len(parsed_url.path)
    QueryLength = len(parsed_url.query)
    DoubleSlashInPath = 1 if '//' in url else 0
    sensitive_words = ["Bank", "Credit", "Password", "Login", "Personal", "Scam", "Phishing", "Malware", "Virus", "Hacking", "Fraud", "Stealing", "Identity", "Plagiarism", "Copyright", "Trademark", "Abortion", "Terrorism", "Child", "Cyberbullying", "Death", "Disease", "Gambling", "Guns", "Infidelity", "Kidnap", "Suicide", "Torture", "Underage", "Weapons", "Wildlife", "Zoosadism", "Addiction", "Alcoholism", "Domestic", "Grief", "Mental", "Poverty", "Racism", "Stalking", "Workplace", "Xenophobia", "Abuse", "Anxiety", "Emotional", "Gang", "Obesity", "Pain", "Advocate", "Agony", "Angry", "Attack", "Betrayal", "Bias", "Bullying", "Catastrophe", "Chaos", "Cheating", "Condemn", "Confusion", "Crazy", "Cruel", "Depression", "Disgusting", "Dysfunction", "Embarrassed", "Failure", "Foul", "Horrible", "Incompetent", "Insane", "Nasty", "Rape", "Repulsive", "Schizophrenic", "Sick", "Stupid", "Ugly", "Violence", "War", "Waste", "Weak", "Worthless", "Abandon", "Admitted", "Betrayal", "Bipolar", "Bullying", "Cancer", "Catastrophe", "Chaos", "Cheating", "Child", "Condemn", "Confusion", "Crazy", "Cruel", "Depressed", "Disgusting", "Dysfunction", "Embarrassed", "Failure", "Foul", "Horrible", "Incompetent", "Insane", "Nasty", "Racist"]
    NumSensitiveWords = sum(1 for word in sensitive_words if word in url.lower())
    EmbeddedBrandName = extract_embedded_brand_name(url)
    PctExtHyperlinks = get_external_links_percentage(url)
    PctExtResourceUrls = calculate_external_resource_percentage(url)
    ExtFavicon = ExtFavicon = 1 if has_external_favicon(url) else 0
    InsecureForms = has_insecure_forms(parsed_url)
    RelativeFormAction = has_relative_form_action(parsed_url)
    
    ExtFormAction=0
    AbnormalFormAction = detect_abnormal_form_action(url)
    PctNullSelfRedirectHyperlinks = detect_pct_null_self_redirect_hyperlinks(url)
    FrequentDomainNameMismatch=0
    FakeLinkInStatusBar = detect_fake_link_in_status_bar(url)
    RightClickDisabled = detect_right_click_disabled(url)
    popup_detected = detect_popup_window(url) 
    SubmitInfoToEmail = detect_submit_info_to_email(url)
    IframeOrFrame = detect_iframe_or_frame(url)
    MissingTitle = detect_missing_title(url)
    ImagesOnlyInForm=0
    
    url_tuple = (
        NumDots, SubdomainLevel, PathLevel, UrlLength, NumDash, NumDashInHostname, AtSymbol, TildeSymbol,
        NumUnderscore, NumPercent, NumQueryComponents, NumAmpersand, NumHash, NumNumericChars, NoHttps, RandomString,
        IpAddress, DomainInSubdomains, DomainInPaths, HttpsInHostname, HostnameLength, PathLength, QueryLength,
        DoubleSlashInPath, NumSensitiveWords, EmbeddedBrandName, PctExtHyperlinks, PctExtResourceUrls, ExtFavicon,
        InsecureForms, RelativeFormAction, ExtFormAction, AbnormalFormAction, PctNullSelfRedirectHyperlinks,
        FrequentDomainNameMismatch, FakeLinkInStatusBar, RightClickDisabled, popup_detected, SubmitInfoToEmail,
        IframeOrFrame, MissingTitle, ImagesOnlyInForm
    )
    return url_tuple

@app.route('/extract_features', methods=['POST'])
def handle_extract_features():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if url:
            features = extract_url_features(url)
            prediction = loaded_model.predict([features])
            return jsonify({'prediction': int(prediction)})
        else:
            return jsonify({'error': 'Invalid URL'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# url_features = extract_url_features(url)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8030)
