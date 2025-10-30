# app.py

import streamlit as st
import os
import requests
import groq  # Using Groq
import wikipedia
import string # For cleaning input
from urllib.parse import quote_plus
from dotenv import load_dotenv

# --- INITIAL SETUP AND CONFIGURATION ---

load_dotenv()

# Configure Groq API
try:
    # Initialize the Groq client
    client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    if not os.getenv("GROQ_API_KEY"):
        st.error("Groq API key not found. Please check your .env file.", icon="🚨")
        st.stop()
except Exception as e:
    st.error(f"Error configuring the Groq API. Details: {e}", icon="🚨")
    st.stop()

# Get the Weather API key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# --- HELPER FUNCTIONS ---

def get_weather_info(city_name, api_key):
    """Fetches real-time weather data from OpenWeatherMap API."""
    if not api_key:
        return "Weather API key not configured."
    
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        weather_desc = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        
        return f"**Weather:** {weather_desc} | **Temp:** {temp}°C | **Feels Like:** {feels_like}°C | **Humidity:** {humidity}%"
    except requests.exceptions.HTTPError:
        return f"Could not find weather for '{city_name}'. Please check the city name."
    except Exception as e:
        return f"Could not retrieve weather data. Error: {e}"

def generate_flight_search_link(city_name):
    """Generates a pre-filled Google Flights search link."""
    query = f"flights to {city_name}"
    encoded_query = quote_plus(query)
    return f"https://www.google.com/search?q={encoded_query}"

def get_city_summary(city_name):
    """Fetches a concise summary of a city from Wikipedia."""
    try:
        summary = wikipedia.summary(city_name, sentences=3, auto_suggest=True)
        return summary
    except Exception:
        return f"Could not find a Wikipedia summary for '{city_name}'."

def generate_travel_guide(city_name):
    """Uses Groq to generate a structured travel guide."""
    prompt = f"""
    Create a concise and exciting travel guide for {city_name}, formatted with these exact headings:
    ### Top 3 Tourist Attractions
    1. [Name]
    ### 3 Local Dishes to Try
    1. [Name]
    ### 3 Popular Malls for Shopping
    1. [Name]
    """
    try:
        response = client.chat.completions.create(
            # FIX: Using a new, active model from Groq
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate guide. AI model error: {e}"

def parse_guide_to_dict(guide_text):
    """Parses the raw text output from the AI into a structured dictionary."""
    guide_dict = {}
    sections = guide_text.split('### ')[1:]
    for section in sections:
        lines = section.strip().split('\n')
        title = lines[0].strip()
        items = [item.split('. ', 1)[1].strip() for item in lines[1:] if '. ' in item]
        guide_dict[title] = items
    return guide_dict

def generate_google_maps_link(item, city):
    """Generates a safe, encoded Google Maps link."""
    query = f"{item}, {city}"
    encoded_query = quote_plus(query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

# --- STREAMLIT UI ---

# FIX: Corrected the closing quote on layout="wide"
st.set_page_config(page_title="Trip Whisperer", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #0E1117; }
    .block-container { max-width: 800px; padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3, p, .stMarkdown, .stTextInput>label { color: #FFFFFF; }
    h1 { text-align: center; }
    .stTextInput>div>div>input { border-radius: 15px; border: 1px solid #30363F; background-color: #0E1117; color: #FFFFFF; padding: 12px; }
    .stButton>button { width: 100%; border-radius: 15px; border: none; background-color: #007BFF; color: white; padding: 12px; transition: background-color 0.3s ease; }
    .stButton>button:hover { background-color: #0056b3; }
    .card { background-color: #161B22; border: 1px solid #30363F; border-radius: 15px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-bottom: 25px; }
    .card h3 { color: #58A6FF; border-bottom: 1px solid #30363F; padding-bottom: 10px; }
    .card a { color: #58A6FF; text-decoration: none; }
    .card a:hover { text-decoration: underline; color: #80BFFF; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- Main Application Flow ---

st.title("Trip Whisperer: Your AI Travel Companion ✈️")
city_input = st.text_input("Enter a city name:", "", label_visibility="collapsed", placeholder="e.g., Paris, Tokyo, New York")

if st.button("Generate Guide") and city_input:
    # FIX: Stripping whitespace AND punctuation (like '.')
    city_input = city_input.strip().strip(string.punctuation)
    
    with st.spinner(f"Conjuring a travel guide for {city_input}... ✨"):
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        weather_info = get_weather_info(city_input, WEATHER_API_KEY)
        st.markdown(f"**Current Weather in {city_input.title()}:**")
        st.write(weather_info)
        
        flight_link = generate_flight_search_link(city_input)
        st.markdown(f"<a href='{flight_link}' target='_blank' style='display:inline-block; margin-top:10px; padding:8px 16px; background-color:#2563EB; color:white; border-radius:10px; text-decoration:none;'>Search for Flights to {city_input.title()}</a>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader(f"A Glimpse into {city_input.title()}")
        summary = get_city_summary(city_input)
        st.write(summary)
        st.markdown("</div>", unsafe_allow_html=True)

        # FIX: Corrected typo from guide_.text
        guide_text = generate_travel_guide(city_input)
        
        if "Could not generate guide" in guide_text:
            st.error(guide_text)
        else:
            parsed_guide = parse_guide_to_dict(guide_text)
            # FIX: Corrected CSS class typo from class'card'
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            for category, items in parsed_guide.items():
                st.subheader(category)
                for item in items:
                    map_link = generate_google_maps_link(item, city_input)
                    st.markdown(f"- [{item}]({map_link})", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.success("Your personalized travel guide is ready! Click any item to explore it on Google Maps.")