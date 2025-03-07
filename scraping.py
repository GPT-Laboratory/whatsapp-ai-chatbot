# scraping.py
import requests
from bs4 import BeautifulSoup

def scrape_text(url):
    """
    Fetches the URL and processes text based on site type.
    If the site is 'nettimokki', extracts specific sections and applies replacements.
    Otherwise, extracts text only from relevant semantic tags and includes image alt text.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()  # Raise error if not 200
        soup = BeautifulSoup(resp.text, "html.parser")

        if "nettimokki" in url:
            # Extract text from the specific div
            content_div = soup.find("div", class_="vif-left-column")
            text = content_div.get_text(separator="\n") if content_div else ""
            
            # Extract and process the characteristic list
            characteristic_list = soup.find("ul", class_="characteristic-list")
            if characteristic_list:
                replacements = {}
                for li in characteristic_list.find_all("li"):
                    feature_name = li.get_text(strip=True)
                    if "block-icon" in li.get("class", []):
                        replacements[feature_name] = f"{feature_name}: Ei, "
                    elif "check-icon" in li.get("class", []):
                        replacements[feature_name] = f"{feature_name}: Kyllä, "
                
                for key, value in replacements.items():
                    text = text.replace(key, value)
                
            # Clean up excessive whitespace
            text = " ".join(text.split())
        else:
            # General case: extract text only from relevant semantic tags
            semantic_tags = [
                "article", "section", "header", "footer", "main", "nav", "aside",
                "h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "figcaption",
                "table", "thead", "tbody", "tfoot", "tr", "th", "td",
                "ul", "ol", "li", "dl", "dt", "dd"
            ]
            semantic_elements = soup.find_all(semantic_tags)
            text = "\n".join(elem.get_text(separator=" ") for elem in semantic_elements)
            
            # Include image alt texts
            image_alts = [img.get("alt", "") for img in soup.find_all("img") if img.get("alt")]
            if image_alts:
                text += "\n\nImage Descriptions:\n" + "\n".join(image_alts)
            
            # Clean up excessive whitespace
            text = " ".join(text.split())
        
        return text
    except Exception as e:
        return f"Could not scrape the link: {e}"
