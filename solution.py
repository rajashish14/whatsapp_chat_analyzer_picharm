import re
from collections import Counter

import emoji
import nltk
from nltk.corpus import stopwords
from pyexpat.errors import messages
from textblob import TextBlob
from urlextract import URLExtract
# Download required NLTK resources (only needed once)
nltk.download('punkt')
nltk.download('stopwords')
def fetch_stats(selected_users, df):
    if selected_users != "Overall":
        df = df[df['users_name'] == selected_users]

    num_messages = df.shape[0]
    words = []
    for message in df['messages']:
        words.extend(message.split())
    num_media = df[df['messages'] == '<Media omitted>\n'].shape[0]
    #fetch number of the links....
    extract = URLExtract()
    links = []
    for message in df['messages']:
        links.extend(extract.find_urls(message))
    return num_messages, len(words), num_media, len(links)


def get_sentiment(selected_users, df):
    if selected_users == 'Overall':
        messages = df['messages'].dropna().astype(str)  # Convert to string
    else:
        messages = df[df['users_name'] == selected_users]['messages'].dropna().astype(str)

    sentiments = messages.apply(lambda msg: analyze_sentiment(msg))
    return sentiments
def analyze_sentiment(message):
    analysis = TextBlob(message)
    polarity = analysis.sentiment.polarity  # Get sentiment score

    # Categorize into Positive, Neutral, Negative
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"


def extract_emojis(text):
    """Extracts all emojis from a given text."""
    return [char for char in text if char in emoji.EMOJI_DATA]
def count_emojis(df, selected_user):
    if selected_user != "Overall":
        df = df[df['users_name'] == selected_user]

    all_messages = ''.join(df['messages'].astype(str))
    all_emojis = []
    for message in all_messages:
        all_emojis.extend(extract_emojis(message))  # Collect all emojis

    emoji_counts = Counter(all_emojis)  # Count occurrences
    return emoji_counts


def get_most_used_word(selected_user, df):
    if selected_user != "Overall":
        df = df[df['users_name'] == selected_user]

    # Convert messages column to a single string
    messages = df[df['messages']!= '<Media omitted>\n'].dropna().str.cat(sep=' ')

    # Tokenize using regex
    tokens = re.findall(r'\b[a-zA-Z]+\b', messages.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]

    # Count token frequency
    token_frequency = Counter(filtered_tokens)

    return token_frequency


def get_wordcloud(selected_user, df):
    if selected_user != "Overall":
        df = df[df['users_name'] == selected_user]
    df = df[df['messages']!= '<Media omitted>\n']
    text = ' '.join(df['messages'])
    return text
