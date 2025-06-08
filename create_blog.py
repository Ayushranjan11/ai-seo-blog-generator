import os
import requests
from dotenv import load_dotenv
import argparse
import google.generativeai as genai

# Load environment variables from the .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# --- Configure the Google Gemini API ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"[FATAL ERROR] Could not configure Google API: {e}")
    exit()

def find_trending_product(query):
    """Fetches a trending product from Google Shopping using SerpApi."""
    print(f"\n[INFO] Step 1: Finding a trending product for query: '{query}'...")
    
    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google_shopping",
        "q": query,
        "tbs": "p_ord:r", # Sort by review rating (trending)
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

        if "shopping_results" in data and len(data["shopping_results"]) > 0:
            # Get the first product
            product = data["shopping_results"][0]
            product_info = {
                "title": product.get("title"),
                "price": product.get("price"),
                "source": product.get("source"), # The store selling it
                "link": product.get("link")
            }
            print(f"-> Found Product: {product_info['title']} from {product_info['source']}")
            return product_info
        else:
            print("[ERROR] No trending products found for this query.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch data from SerpApi: {e}")
        return None

def get_seo_keywords(product_info):
    """Generates SEO keywords for the product using the Google Gemini API."""
    print("[INFO] Step 2: Generating SEO keywords with Gemini AI...")
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an SEO expert. Based on the following product information, generate 3-4 relevant, long-tail SEO keywords.
    These keywords should be what a customer might search for when looking to buy this product.
    Return only the keywords, separated by commas. Do not add any extra text or labels.

    Product Title: {product_info['title']}
    Product Price: {product_info['price']}
    Sold By: {product_info['source']}
    """
    
    try:
        response = model.generate_content(prompt)
        keywords = [keyword.strip() for keyword in response.text.split(',')]
        print(f"-> Keywords generated: {', '.join(keywords)}")
        return keywords
    except Exception as e:
        print(f"[ERROR] Failed to generate keywords from Google Gemini: {e}")
        return None

def create_blog_post(product_info, keywords):
    """Creates a short blog post using the product info and SEO keywords."""
    print("[INFO] Step 3: Writing blog post with Gemini AI...")
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are a friendly and persuasive blog writer. Write a short blog post of about 150-200 words for the following product.
    The tone should be enthusiastic and helpful.
    Start with an engaging headline.
    Naturally incorporate the following SEO keywords into the text: {', '.join(keywords)}.
    End with a call to action inviting readers to check out the product link.

    Product Title: {product_info['title']}
    Price: {product_info['price']}
    Available at: {product_info['source']}
    """

    try:
        response = model.generate_content(prompt)
        blog_content = response.text.strip()
        print("-> Blog post written successfully.")
        return blog_content
    except Exception as e:
        print(f"[ERROR] Failed to write blog post from Google Gemini: {e}")
        return None

def save_as_markdown(product_info, blog_content):
    """Saves the blog post as a clean Markdown file."""
    print("[INFO] Step 4: Saving blog post as a Markdown file...")
    # Create a clean filename from the product title
    safe_filename = "".join(x for x in product_info['title'] if x.isalnum() or x in " _-").rstrip()
    filename = f"{safe_filename}.md"

    # Add the product link at the end for the call to action
    full_content = f"{blog_content}\n\n---\n\n**Find it here:** [{product_info['title']}]({product_info['link']})"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"\n[SUCCESS] Blog post saved as '{filename}'!")
        print("You can now copy the content of this file and paste it into Medium, WordPress, or any other platform.")
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")

def main():
    """Main function to orchestrate the blog creation pipeline."""
    parser = argparse.ArgumentParser(description="AI SEO Blog Post Creation Tool")
    parser.add_argument("--query", type=str, required=True, help="The type of product to search for (e.g., 'best running shoes').")
    args = parser.parse_args()
    
    product = find_trending_product(args.query)
    
    if product:
        keywords = get_seo_keywords(product)
        if keywords:
            blog_post = create_blog_post(product, keywords)
            if blog_post:
                save_as_markdown(product, blog_post)

if __name__ == "__main__":
    main()