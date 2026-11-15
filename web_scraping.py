
import requests
import pandas as pd
import time

from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

# Website details
BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")

USER_AGENT = "StudentWebScraper/1.0"
MAX_PAGES = 3

# Rating conversion
ratings = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

# Create a session
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


# Step 1: Check robots.txt
def check_robots():

    response = session.get(ROBOTS_URL, timeout=15)

    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)

    if response.status_code == 404:
        print("robots.txt not found. No published rules.")
        parser.parse([])

    else:
        response.raise_for_status()
        parser.parse(response.text.splitlines())

    return parser


# Step 2: Scrape book information
def scrape_books():

    robots = check_robots()

    current_url = START_URL
    all_books = []

    for page in range(1, MAX_PAGES + 1):

        # Check permission before requesting page
        if not robots.can_fetch(USER_AGENT, current_url):
            print("Scraping not allowed:", current_url)
            break

        print(f"Scraping page {page}...")

        response = session.get(current_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        books = soup.select("article.product_pod")

        if not books:
            print("No books found. Stopping.")
            break

        for book in books:

            title_tag = book.select_one("h3 a")
            price_tag = book.select_one("p.price_color")
            stock_tag = book.select_one("p.availability")
            rating_tag = book.select_one("p.star-rating")

            if not all([title_tag, price_tag, stock_tag, rating_tag]):
                continue

            title = title_tag.get("title", title_tag.get_text(strip=True))

            price = price_tag.get_text(strip=True)

            availability = stock_tag.get_text(strip=True)

            rating_class = rating_tag.get("class", [])
            rating_word = next(
                (r for r in rating_class if r in ratings),
                None
            )

            rating = ratings.get(rating_word)

            book_url = urljoin(
                response.url,
                title_tag.get("href")
            )

            all_books.append({
                "Title": title,
                "Price": price,
                "Availability": availability,
                "Rating": rating,
                "URL": book_url
            })

        # Find next page
        next_page = soup.select_one("li.next a")

        if next_page:
            current_url = urljoin(
                response.url,
                next_page.get("href")
            )
        else:
            break

        # Wait before next request
        time.sleep(2)

    return all_books


# Step 3: Save data into CSV
try:

    data = scrape_books()

    if data:

        df = pd.DataFrame(data)

        df.to_csv(
            "books_data.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print("\nScraping completed successfully!")
        print("Total books scraped:", len(df))
        print("CSV file saved as books_data.csv")

        print("\nFirst 5 records:")
        print(df.head())

    else:
        print("No data collected.")

except requests.exceptions.RequestException as error:
    print("Website connection error:", error)

except Exception as error:
    print("Unexpected error:", error)

finally:
    session.close()
