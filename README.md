# CryptoPanicScraper

## Overview
CryptoPanicScraper is an asynchronous web scraper that gathers cryptocurrency-related news from the CryptoPanic website, analyzes sentiment using the NLTK VADER sentiment analysis tool, and caches the data for reuse. The scraper allows users to specify a topic, set a filter, limit the number of articles, and customize other parameters for news collection.

## Features

- **Topic Search**: Search for news related to specific cryptocurrencies or topics.
- **Sentiment Analysis**: Perform sentiment analysis using the VADER model, enhanced with custom financial terms.
- **Caching**: Caches previously scraped articles to avoid duplicating data in subsequent runs.
- **Pagination Handling**: Automatically scrolls or clicks the "Load More" button to fetch additional articles.
- **Data Storage**: Saves scraped news data locally in a file for persistence.


## Parameters
- **filter (optional): String filter for the type of news (all, bullish, bearish, etc.). Defaults to None.
- **limit (optional): Integer limit for the number of articles to scrape. Defaults to 10.
- **topic (optional): String topic to search for specific cryptocurrency news. Defaults to None.
- **save_path (optional): Path to save the cached and scraped data. Defaults to 'news_data'.

## Methods
- **_update_vader_lexicon(self): Updates the VADER sentiment lexicon with custom financial terms.
- **load_cached_data(self): Loads cached articles from a pickle file if available.
- **async run(self): Initiates the scraper, navigates to the CryptoPanic page, and collects data.
- **async search_topic(self, page, topic): Searches for a specific topic using CryptoPanic's search bar.
- **async collect_data(self, page): Collects news articles from the page, including sentiment analysis.
- **async get_news_sentiment(self, symbol: str): Fetches sentiment data for a specific cryptocurrency symbol.
- **async load_more(self, page): Scrolls or clicks the "Load More" button to load more content on the page.
- **async retry_fetch_text(self, element, selector, default_value, retries=2): Retries fetching text content with error handling.
- **async retry_fetch_attribute(self, element, selector, attribute, default_value, retries=2): Retries fetching an attribute (e.g., href) with error handling.
- **async get_currencies(self, element): Extracts the mentioned cryptocurrencies from the article.
- **async get_votes(self, element): Extracts vote data such as bullish, bearish, and other vote counts.
- **analyze_sentiment_with_vader(self, title): Performs sentiment analysis on an article title using VADER.
- **save_data(self): Saves the scraped data to a file, merging new data with cached data.

## Requirements

To use this scraper, you need to have the following installed:

- `python` (>=3.8)
- `asyncio`
- `nltk`
- `playwright`
- `pickle`
- `pathlib`
- `logging`

