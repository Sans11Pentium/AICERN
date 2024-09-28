import time
import requests
from flask import Flask, request, jsonify
import pandas as pd
import os
import json
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_sentiment(review):
    api_key = app.config.get('GROQ_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
    'model': 'mixtral-8x7b-32768',
    'messages': [
        {
            'role': 'system', 
            'content': (
                "You are a sentiment analysis classifier. Your task is to analyze the user's input and return a JSON object "
                "formatted response that strictly includes sentiment scores in decimal percentages for 'positive', 'negative', "
                "and 'neutral' sentiments. The format must be: { 'positive': x, 'negative': y, 'neutral': z }. "
                "Do not include any additional text, comments, or explanations. If you cannot provide valid scores, "
                "return an error JSON object instead."
                "dont include anything like : Sure, I can do that/Based on the given text/ Here is an example of how I would respond to a user's input:"
                "dont include any text like : The instructions were very unclear. : I'm ready to analyze the user's input. Here's an example of how I would respond:"
                "dont include any text like  I'm a text-based AI model and I don't have real-time sentiment analysis capabilities. However, I can provide a sample response based on a given text."
                "just give the best possible estimate without worrying that you are a LLM model"
            )
        },
        {'role': 'user', 'content': review}
    ],
    'max_tokens': 50
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        if response.status_code == 429: 
            return 'rate_limit_error'
        response.raise_for_status()  
        sentiment = response.json()['choices'][0]['message']['content']
        # print(sentiment)
        return sentiment
        
        # print(review, json_data["positive"], json_data["negative"], json_data["neutral"])

    except requests.RequestException as e:
        print(f"Error in Groq API request: {e}")
        return "error occured while making an API call"

@app.route('/analyze', methods=['POST'])
def analyze_reviews():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file, please send a file in your requset to get a response'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:  
                df = pd.read_excel(filepath)
            
            reviews = df.iloc[:, 0].tolist()  

            sentiments = []
            i = 0
            delay = 10 
            
            while i < len(reviews):
                sentiment = analyze_sentiment(reviews[i])
                # json_data = json.loads(sentiment)
                print(reviews[i], ":", sentiment)
                if sentiment == 'rate_limit_error':
                    print(f"Rate limit reached, retrying after {delay} seconds...")
                    time.sleep(delay)
                    delay = min(60, delay * 2) 
                else:
                    sentiments.append(sentiment)
                    i += 1
                    delay = 10 
            
            os.remove(filepath)  # remove file once analysis is done
            return jsonify(sentiments)
        
        except Exception as e:
            os.remove(filepath) 
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)