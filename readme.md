# Sentiment Analysis API with Flask

This project implements a Sentiment Analysis API using **Flask**. It allows users to upload files containing reviews in `.csv` or `.xlsx` formats. Each review is processed using the **Groq API** to analyze its sentiment, and the results are returned as JSON objects containing sentiment scores for **positive**, **negative**, and **neutral** categories.

## Features
- Upload `.csv` or `.xlsx` files for sentiment analysis.
- Analyze sentiment using **Groq API**.
- Retry mechanism with **rate limit handling** (for status code `429`).
- Secure configuration using **dotenv** for API keys.
- Modular and reusable code structure.

## Technologies Used
- **Flask**: Web framework for building the API.
- **Pandas**: To handle CSV/Excel file processing.
- **Requests**: To make HTTP requests to the external Groq API.
- **dotenv**: For secure management of environment variables.