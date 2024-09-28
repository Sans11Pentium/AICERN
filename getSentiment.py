import time
import requests
from flask import Flask, request, jsonify
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
GROQ_API_KEY = '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'
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_sentiment(review):
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'mixtral-8x7b-32768',
        'messages': [
            {'role': 'system', 'content': "You are a sentiment analysis classifier. For each review, classify it strictly as either 'positive', 'negative', or 'neutral' based on the overall sentiment of the review. Do not provide any explanation, just return the classification."},
            {'role': 'user', 'content': review}
        ],
        'max_tokens': 1
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        
        if response.status_code == 429:  # Rate limit hit
            return 'rate_limit_error'
        
        response.raise_for_status()  # Raise an error for 4xx/5xx codes
        
        sentiment = response.json()['choices'][0]['message']['content'].strip().lower()
        if sentiment in ['positive', 'negative', 'neutral']:
            return sentiment
        else:
            return 'neutral'  # Default to neutral if something unexpected
        
    except requests.RequestException as e:
        print(f"Error in Groq API request: {e}")
        return 'neutral'  # Default to neutral on error

@app.route('/analyze', methods=['POST'])
def analyze_reviews():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:  # Excel file
                df = pd.read_excel(filepath)
            
            reviews = df.iloc[:, 0].tolist()  # Assuming reviews are in the first column
            sentiments = []
            i = 0
            delay = 10  # Start with a 10-second delay for rate limit
            
            while i < len(reviews):
                sentiment = analyze_sentiment(reviews[i])
                print(reviews[i], ":", sentiment)
                if sentiment == 'rate_limit_error':
                    print(f"Rate limit reached, retrying after {delay} seconds...")
                    time.sleep(delay)
                    delay = min(60, delay * 2)  # Exponential backoff, up to 60 seconds
                else:
                    sentiments.append(sentiment)
                    i += 1
                    delay = 10  # Reset delay after a successful API call
            
            os.remove(filepath)  # Clean up the uploaded file
            return jsonify(sentiments)
        
        except Exception as e:
            os.remove(filepath)  # Clean up in case of error
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
