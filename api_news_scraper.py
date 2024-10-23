import asyncio
import os
import pickle
import pathlib
from playwright.async_api import async_playwright
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from logging_config import logger

class CryptoPanicScraper:
    SCROLL_PAUSE_TIME = 2000  # 2 seconds for page load pause

    def __init__(self, filter= None, limit=10, topic=None, save_path='news_data'):
        self.filter = filter
        self.limit = limit
        self.topic = topic  # New parameter for topic
        self.save_path = save_path
        self.data = []
        self.cached_data = self.load_cached_data()  # Load cached data at initialization
        self.vader_analyzer = SentimentIntensityAnalyzer()  # Initialize VADER analyzer for sentiment analysis
        self._update_vader_lexicon()

    def _update_vader_lexicon(self):
        """Updates VADER lexicon with custom financial terms and their sentiment scores."""
        financial_terms = {
            "profit": 2.0,
            "loss": -2.0,
            "gain": 1.5,
            "surge": 2.0,
            "collapse": -2.5,
            "plummet": -2.5,
            "bullish": 2.5,
            "bearish": -2.5,
            "recession": -3.0,
            "growth": 2.0,
            "decline": -1.5,
            "invest": 1.5,
            "inflation": -2.0,
            "revenue": 1.5,
            "downgrade": -2.0,
            "upgrade": 1.8,
            "outperform": 2.0,
            "underperform": -2.0,
            "volatile": -1.5,
            "fiscal": 1.2
        }
        self.vader_analyzer.lexicon.update(financial_terms)
        logger.info("Updated VADER lexicon with financial terms.")

    def load_cached_data(self):
        """Load previously scraped data (cached data) from the file if it exists."""
        file_name = f"cryptopanic_{self.filter}_cache.pickle"
        file_path = os.path.join(self.save_path, file_name)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                logger.info(f"Loaded cached data from {file_path}")
                return pickle.load(f)
        logger.info("No cached data found.")
        return {}

    async def run(self):
        """Run the scraper."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            url = f"https://www.cryptopanic.com/news?filter={self.filter}"
            logger.info(f"Navigating to {url}")
            await page.goto(url)

            # If topic is provided, perform the search
            if self.topic:
                await self.search_topic(page, self.topic)

            await self.collect_data(page)

            await browser.close()

            # Save the collected data to a file if there are new articles
            if self.data:
                self.save_data()


    async def get_news_sentiment(self, symbol: str):
        """Fetch sentiment data for a given symbol."""
        self.topic = symbol  # Set topic to the requested symbol
        await self.run()  # Run the scraper to fetch news
        return self.data  # Return the collected data
    
    async def search_topic(self, page, topic):
        """Search for a specific topic using the search bar."""
        try:
            # Locate the search input element and enter the topic
            search_input = await page.query_selector('#acSearchInput')
            if search_input:
                logger.info(f"Searching for topic: {topic}")
                await search_input.fill(topic)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)  # Give some time for results to load

                # Optionally click the first relevant result
                first_result = await page.query_selector(".ac__entry.ac__selected")
                if first_result:
                    await first_result.click()
                    logger.info(f"Clicked on the first search result for topic: {topic}")
                    await page.wait_for_timeout(2000)
            else:
                logger.warning("Search input not found.")
        except Exception as e:
            logger.error(f"Failed to search for topic: {e}")

    async def collect_data(self, page):
        """Collect data from the page."""
        retries = 0
        max_retries = 2
        loaded_elements = 0

        while loaded_elements < self.limit and retries < max_retries:
            # Load more content if possible
            await self.load_more(page)

            articles = await page.query_selector_all('div.news-row.news-row-link')
            loaded_elements = len(articles)
            logger.info(f"Loaded {loaded_elements} articles so far.")

            # If enough articles are loaded, stop
            if loaded_elements >= self.limit:
                break

            retries += 1
            logger.warning(f"Retry {retries}/{max_retries} to load more articles.")

        if loaded_elements == 0:
            logger.error("No articles loaded.")
            return

        logger.info(f"Processing {loaded_elements} articles.")

        # Process each article
        for i, article in enumerate(articles[:self.limit]):
            try:
                # Extract title
                title = await self.retry_fetch_text(article, "span.title-text span", "Untitled")

                # Skip untitled articles
                if title == "Untitled":
                    logger.info(f"Skipping article {i+1}: No title found.")
                    continue

                # Extract URL
                source_url = await self.retry_fetch_attribute(article, "a.news-cell.nc-title", 'href', "N/A")

                # Skip already cached articles
                if source_url in self.cached_data:
                    logger.info(f"Skipping article {i+1}: Already cached.")
                    continue

                # Extract date
                date_time = await self.retry_fetch_attribute(article, 'time', 'datetime', 'N/A')

                # Extract source
                source_name = await self.retry_fetch_text(article, "span.si-source-domain", "Unknown")

                # Extract currencies
                currencies = await self.get_currencies(article)

                # Extract votes
                votes = await self.get_votes(article)

                # Perform sentiment analysis on the title
                sentiment, confidence = self.analyze_sentiment_with_vader(title)

                # Prepare data entry
                article_data = {
                    "Date": date_time,
                    "Title": title,
                    "Currencies": currencies,
                    "Votes": votes,
                    "Source": source_name,
                    "URL": source_url,
                    "Sentiment": sentiment,
                    "Confidence": confidence,
                }

                self.data.append(article_data)
                logger.info(f"Scraped article {i+1}: {title} - {sentiment} - {confidence}%")

            except Exception as e:
                logger.error(f"Error scraping article {i+1}: {e}")

        logger.info(f"Finished gathering {len(self.data)} rows of data.")

    async def load_more(self, page):
        """Load more content by scrolling down or clicking 'Load More'."""
        try:
            # Check if there's a 'Load More' button and click it if it exists
            load_more_button = await page.query_selector('.btn-outline-primary')
            if load_more_button:
                await load_more_button.click()
                logger.info("Clicked 'Load More' button.")
            else:
                # If no 'Load More' button, simulate scrolling
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                logger.info("Scrolled to the bottom of the page.")

            # Wait for the new content to load
            await page.wait_for_timeout(self.SCROLL_PAUSE_TIME)

        except Exception as e:
            logger.error(f"Failed to load more content: {e}")

    async def retry_fetch_text(self, element, selector, default_value, retries=2):
        """Retry fetching text content from an element."""
        attempt = 0
        while attempt < retries:
            try:
                elem = await element.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text:
                        return text.strip()
            except Exception as e:
                logger.warning(f"Retry {attempt+1}/{retries} fetching text for {selector}: {e}")
            attempt += 1
            await asyncio.sleep(1)

        logger.warning(f"Failed to fetch text for {selector} after {retries} retries. Using default: '{default_value}'")
        return default_value

    async def retry_fetch_attribute(self, element, selector, attribute, default_value, retries=2):
        """Retry fetching an attribute from an element."""
        attempt = 0
        while attempt < retries:
            try:
                elem = await element.query_selector(selector)
                if elem:
                    attr = await elem.get_attribute(attribute)
                    if attr:
                        return attr.strip()
            except Exception as e:
                logger.warning(f"Retry {attempt+1}/{retries} fetching attribute {attribute} for {selector}: {e}")
            attempt += 1
            await asyncio.sleep(1)

        logger.warning(f"Failed to fetch attribute {attribute} for {selector} after {retries} retries. Using default: '{default_value}'")
        return default_value

    async def get_currencies(self, element):
        """Fetch currencies linked to the article."""
        try:
            currency_elements = await element.query_selector_all("a.colored-link")
            currencies = [await currency.inner_text() for currency in currency_elements]
            return currencies if currencies else ['No currency']
        except Exception as e:
            logger.warning(f"Failed to fetch currencies: {e}")
            return ['No currency']

    async def get_votes(self, element):
        """Extract vote data."""
        votes = {}
        try:
            vote_elements = await element.query_selector_all("span.nc-vote-cont")
            for vote_element in vote_elements:
                vote_title = await vote_element.get_attribute('title')
                if vote_title:
                    value = vote_title[:2]
                    action = vote_title.replace(value, '').replace('votes', '').strip()
                    votes[action] = int(value)
        except Exception as e:
            logger.warning(f"Failed to fetch votes: {e}")
        return votes

    def analyze_sentiment_with_vader(self, title):
        """Uses VADER to analyze sentiment for a given article title."""
        vader_scores = self.vader_analyzer.polarity_scores(title)
        compound_score = vader_scores['compound']

        # Enhanced thresholds for sentiment classification
        if compound_score >= 0.6:
            sentiment = 'very bullish'
        elif 0.1 <= compound_score < 0.6:
            sentiment = 'bullish'
        elif -0.1 < compound_score < 0.1:
            sentiment = 'neutral'
        elif -0.6 < compound_score <= -0.1:
            sentiment = 'bearish'
        else:
            sentiment = 'very bearish'

        confidence = int((abs(compound_score) ** 0.5) * 100)  # Confidence boost for more extreme scores
        title_length_factor = max(0.8, min(len(title) / 50, 1.2))  # Adjust based on length, clamped between 0.8 and 1.2
        confidence = int(confidence * title_length_factor)
        return sentiment, max(0, min(confidence, 100))  # Ensure confidence is within 0-100

    def save_data(self):
        """Save the scraped data to a file, merging with cached data."""
        # Merge the new data with cached data
        for article in self.data:
            self.cached_data[article['URL']] = article

        # Save both the new and cached data
        pathlib.Path(self.save_path).mkdir(parents=True, exist_ok=True)
        file_name = f"cryptopanic_{self.filter}_cache.pickle"
        file_path = os.path.join(self.save_path, file_name)

        with open(file_path, 'wb') as f:
            pickle.dump(self.cached_data, f)

        logger.info(f"Data saved to {file_path}")

# # Usage example
# scraper = CryptoPanicScraper()
# scraper.filter = 'all'
# scraper.limit = 50
# scraper.topic = 'BTC'

# # Run the scraper asynchronously
# asyncio.run(scraper.run())
