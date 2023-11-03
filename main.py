""""
An API created using python FastAPI framework to scrap climate change data
and classify whether true or false.
"""

from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import re
from newspaper import Article
from fastapi.responses import JSONResponse
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="News Classification API",
    description="An Api that scraps news content from the internet and classifies whether True or False",
    version="0.1.0",
    openapi_url="/api/v0.1.1/openapi.json",
)

# configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Array of useful websites in Kenya to scrap climate blogs
newspapers = [
    {
        "name": "nation-africa",
        "address": "https://nation.africa/service/search/kenya/290754?query=climate%20change",
        "base": "https://nation.africa",
    },
    {
        "name": "standardmedia-ke",
        "address": "https://www.standardmedia.co.ke/environment-climate/",
        "base": "",
    },
    {
        "name": "world-bank",
        "address": "https://blogs.worldbank.org/search?f%5B0%5D=topic%3A282&f%5B1%5D=language%3Aen",
        "base": "https://blogs.worldbank.org",
    },
    {
        "name": "tuko-news",
        "address": "https://www.tuko.co.ke/tags/climate-change/",
        "base": "",
    },
]


# An endpoint for /home
@app.get("/")
def welcome():
    """
    Welcome awesome user😀, this is where it all happens. We are the GreenCode-Titans.
    """
    return {"message": "Welcome to GreenCodeTitans Climate Change News API"}


# Define the list of excluded URLs
# These urls do not point to custom news pages, so we exclude them
excluded_urls = {
    "https://www.tuko.co.ke/tags/climate-change/?page=2",
    "https://www.tuko.co.ke/tags/climate-change/",
    "https://blogs.worldbank.org/search?f%5B0%5D=topic%3A282&f%5B1%5D=language%3Aen",
    "https://blogs.worldbank.org/search?f%5B0%5D=language%3Aen",
    "https://www.standardmedia.co.ke/category/63/environment",
    "https://nation.africa/service/search/kenya/290754?pageNum=1&query=climate%20change",
    "https://blogs.worldbank.org/search?f%5B0%5D=topic%3A282&f%5B1%5D=language%3Aen",
    "https://nation.africa/kenya/videos/news/stakeholders-decry-gender-inequality-in-climate-change-policies-2374246",
}


# An API endpoint to fetch only 100 news from Kenyan websites.
@app.get("/news")
def get_news():
    """
    This endpoint crawls the internet scraping news information from the above news pages.

    Args:
        None.

    Returns:
        dict: A JSON response with the news body content,url, title and source and prediction result.
    """
    articles = []
    unique_urls = set()  # To keep track of unique article URLs

    # Define a counter to keep track of the number of articles collected.
    article_count = 0

    for newspaper in newspapers:
        if article_count >= 50:
            break  # Exit the loop once you have 50 articles.

        response = requests.get(newspaper["address"])
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a"):
                href = a_tag.get("href", "")
                url = None  # Initialize url as None

                # Check if the text within the <a> tag matches the keywords
                if re.search(
                    r"(climate|carbon|global-warming)", a_tag.text, re.IGNORECASE
                ):
                    url = href
                # Check if the href attribute matches the keywords
                elif re.search(r"(climate|carbon|global-warming)", href, re.IGNORECASE):
                    url = href

                if url:  # Check if url is not None
                    if (
                        url not in unique_urls and url not in excluded_urls
                    ):  # Check for uniqueness and exclusion
                        if article_count >= 50:
                            break  # Exit the loop once you have 50 articles.
                        title = a_tag.text.strip().replace("\n", "")
                        if title:
                            # Start classifying the content
                            try:
                                m_article = {
                                    "title": title,
                                    "url": newspaper["base"] + url
                                    if newspaper["base"]
                                    else url,
                                    "source": newspaper["name"],
                                }
                                articles.append(m_article)
                                article_count += 1
                            except Exception as e:
                                print("Error", e)
                        # Add the URL to the set to track unique articles
                        unique_urls.add(url)
    # Include the total count of articles in the response.
    response_data = {
        "articles": articles,
        "total_count": article_count,  # Include the count in the response
    }

    all_resp_list = []
    for article in response_data["articles"]:
        try:
            all_res = classify_by_url(article)
            all_resp_list.append(all_res)
            all_resp_list = [
                article
                for article in all_resp_list
                if article.get("classified_as") == "TRUE"
            ]

        except Exception as e:
            print("Error in news classification", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred" + e,
            )
    # Write the latest news to .json file to cache directory so as to minimize on latency
    with open("cache/articles.json", "w") as json_file:
        json.dump(all_resp_list, json_file)

    return all_resp_list


# Creating a function to handle
def classify_by_url(_article):
    """Submit a url for news classification"""

    API_URL = "https://api-inference.huggingface.co/models/MYC007/Real-and-Fake-News-Detection"
    key = os.getenv("huggingface_api_key")
    headers = {"Authorization": "Bearer " + key}

    article = Article(_article["url"], language="en")
    article.download()
    article.parse()
    content = article.text.strip().replace("\n", "")
    article.nlp()  # use natural language processing
    summary = article.summary  # get the summary

    news_content = json.dumps({"inputs": summary})

    try:
        response = requests.post(API_URL, headers=headers, json=news_content)
        response_json = response.json()
        # Extract the label with the highest score
        classification = max(response_json[0], key=lambda x: x["score"])["label"]
        if classification == "LABEL_0":
            result = "FAKE"
        elif classification == "LABEL_1":
            result = "TRUE"
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Try Again. Model is being initialized!" + e,
        )

    res = {
        "title": _article["title"],
        "content": content,
        "source": _article["source"],
        "url": _article["url"],
        "classified_as": result,
    }
    # return JSONResponse(content=res)
    return res


class NewsInput(BaseModel):
    input_text: str


# Replace this function with your prediction logic
def make_prediction(text):
    news_content = json.dumps({"inputs": text})
    API_URL = "https://api-inference.huggingface.co/models/MYC007/Real-and-Fake-News-Detection"

    # Fetch API key from azure key vault
    key = os.getenv("huggingface_api_key")
    headers = {"Authorization": "Bearer " + key}

    try:
        response = requests.post(API_URL, headers=headers, json=news_content)
        response_json = response.json()
        # Extract the label with the highest score
        prediction_result = max(response_json[0], key=lambda x: x["score"])["label"]
        if prediction_result == "LABEL_0":
            result = "FAKE"
        elif prediction_result == "LABEL_1":
            result = "TRUE"
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Try Again. Model is being initialized!" + e,
        )


# Test individual news article
@app.post("/predict_single/")
def predict_single_news(news_input: NewsInput):
    """
    Make a prediction based on the input text.

    Args:
        text (str): The input text for prediction.

    Returns:
        dict: A JSON response with the input text and prediction result.
    """
    prediction_result = make_prediction(news_input.input_text)
    return {"text": news_input.input_text, "prediction": prediction_result}


# An endpoint to read the json cached file
@app.get("/get_cached_news/")
def fetch_cached_articles():
    """
    To minimize web scraping latency, we return previously classified(cached) articles

    Args:
        None

    Returns:
        dict: A JSON response with the news body content,url, title and source and prediction result.
    """
    # Read the JSON file
    # Check if the JSON file exists
    if os.path.exists("cache/articles.json"):
        with open("cache/articles.json", "r") as json_file:
            loaded_data = json.load(json_file)
        return loaded_data
    else:
        # Return a 404 Not Found response
        raise HTTPException(
            status_code=404,
            detail="File not found. Please try calling the /news endpoint.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
