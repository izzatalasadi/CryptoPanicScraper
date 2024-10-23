# CryptoPanicScraper

CryptoPanicScraper is an asynchronous Python web scraper that gathers cryptocurrency-related news from [CryptoPanic](https://cryptopanic.com/). It provides sentiment analysis for the news headlines using the NLTK VADER sentiment analysis tool and caches the scraped data for future use.

## Features

- **Topic Search**: Search for news related to specific cryptocurrencies or topics.
- **Sentiment Analysis**: Perform sentiment analysis using the VADER model, enhanced with custom financial terms.
- **Caching**: Caches previously scraped articles to avoid duplicating data in subsequent runs.
- **Pagination Handling**: Automatically scrolls or clicks the "Load More" button to fetch additional articles.
- **Data Storage**: Saves scraped news data locally in a file for persistence.

## Requirements

To use this scraper, you need to have the following installed:

- `python` (>=3.8)
- `asyncio`
- `nltk`
- `playwright`
- `pickle`
- `pathlib`
- `logging`

### Install required packages:

```bash
pip install -r requirments.txt
