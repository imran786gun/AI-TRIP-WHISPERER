# app.py

import streamlit as st
import os
import requests
import groq
import wikipedia
import string
import re # Using regular expressions for a smarter parser
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime

# --- INITIAL SETUP AND CONFIGURATION ---

load_dotenv()

# Configure Groq API
try:
    groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    if not os.getenv("GROQ_API_KEY"):
        st.error("Groq API key not found. Please check your .env file.", icon="🚨")
        st.stop()
except Exception as e:
    st.error(f"Error configuring the Groq API. Details: {e}", icon="🚨")
    st.stop()

# Get the Weather API key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# --- TRANSLATIONS DICTIONARY ---
translations = {
    "en": {
        "title": "Trip Whisperer: Your AI Travel Companion ✈️",
        "placeholder": "e.g., Paris, Tokyo, New York",
        "button": "Generate Guide",
        "spinner": "Conjuring a travel guide for {city_name}... ✨",
        "weather_header": "Current Weather in {city_name}:",
        "flights_button": "Search for Flights to {city_name}",
        "summary_header": "A Glimpse into {city_name}",
        "summary_error": "Could not find a Wikipedia summary for '{city_name}' (language: {lang_code}).",
        "guide_error": "Could not generate guide. AI model error: {e}",
        "success": "Your personalized travel guide is ready! Click any item to explore it on Google Maps.",
        "lang_name": "English",
        "lang_select": "Select Language",
        "footer": "Created by Sheikh Imran © 2025. All rights reserved.",
        "download_button": "Download Guide as .txt"
    },
    "es": {
        "title": "Susurrador de Viajes: Tu Compañero de IA ✈️",
        "placeholder": "ej., París, Tokio, Nueva York",
        "button": "Generar Guía",
        "spinner": "Conjurando una guía de viaje para {city_name}... ✨",
        "weather_header": "Tiempo actual en {city_name}:",
        "flights_button": "Buscar Vuelos a {city_name}",
        "summary_header": "Un Vistazo a {city_name}",
        "summary_error": "No se pudo encontrar un resumen de Wikipedia para '{city_name}' (idioma: {lang_code}).",
        "guide_error": "No se pudo generar la guía. Error del modelo de IA: {e}",
        "success": "¡Tu guía de viaje personalizada está lista! Haz clic en cualquier elemento para explorarlo en Google Maps.",
        "lang_name": "Español",
        "lang_select": "Seleccionar Idioma",
        "footer": "Creado por Sheikh Imran © 2025. Todos los derechos reservados.",
        "download_button": "Descargar Guía como .txt"
    },
    "hi": {
        "title": "ट्रिप व्हिस्परर: आपका AI यात्रा साथी ✈️",
        "placeholder": "जैसे, पेरिस, टोक्यो, न्यूयॉर्क",
        "button": "गाइड तैयार करें",
        "spinner": "{city_name} के लिए एक यात्रा गाइड तैयार की जा रही है... ✨",
        "weather_header": "{city_name} में वर्तमान मौसम:",
        "flights_button": "{city_name} के लिए उड़ानें खोजें",
        "summary_header": "{city_name} की एक झलक",
        "summary_error": "'{city_name}' के लिए विकिपीडिया सारांश नहीं मिल सका (भाषा: {lang_code}).",
        "guide_error": "गाइड उत्पन्न नहीं हो सका। AI मॉडल त्रुटि: {e}",
        "success": "आपकी व्यक्तिगत यात्रा गाइड तैयार है! Google मानचित्र पर इसका पता लगाने के लिए किसी भी आइटम पर क्लिक करें।",
        "lang_name": "हिंदी",
        "lang_select": "भाषा चुनें",
        "footer": "शेख इमरान द्वारा निर्मित © 2025. सर्वाधिकार सुरक्षित।",
        "download_button": "गाइड को .txt के रूप में डाउनलोड करें"
    },
    "fr": {
        "title": "Murmure de Voyage : Votre Compagnon IA ✈️",
        "placeholder": "ex: Paris, Tokyo, New York",
        "button": "Générer le Guide",
        "spinner": "Préparation d'un guide de voyage pour {city_name}... ✨",
        "weather_header": "Météo actuelle à {city_name} :",
        "flights_button": "Rechercher des vols vers {city_name}",
        "summary_header": "Un aperçu de {city_name}",
        "summary_error": "Impossible de trouver un résumé Wikipedia pour '{city_name}' (langue : {lang_code}).",
        "guide_error": "Impossible de générer le guide. Erreur du modèle IA : {e}",
        "success": "Votre guide de voyage personnalisé est prêt ! Cliquez sur un élément pour l'explorer sur Google Maps.",
        "lang_name": "Français",
        "lang_select": "Choisir la langue",
        "footer": "Créé par Sheikh Imran © 2025. Tous droits réservés.",
        "download_button": "Télécharger le guide en .txt"
    },
    "te": {
        "title": "ట్రిప్ విస్పరర్: మీ AI ప్రయాణ సహచరుడు ✈️",
        "placeholder": "ఉదా., పారిస్, టోక్యో, న్యూయార్క్",
        "button": "గైడ్ రూపొందించు",
        "spinner": "{city_name} కోసం ప్రయాణ గైడ్‌ను సిద్ధం చేస్తోంది... ✨",
        "weather_header": "{city_name}లో ప్రస్తుత వాతావరణం:",
        "flights_button": "{city_name} కోసం విమానాలను శోధించండి",
        "summary_header": "{city_name} యొక్క సంగ్రహావలోకనం",
        "summary_error": "'{city_name}' కోసం వికీపీడియా సారాంశం కనుగొనబడలేదు (భాష: {lang_code}).",
        "guide_error": "గైడ్ రూపొందించబడలేదు. AI మోడల్ లోపం: {e}",
        "success": "మీ వ్యక్తిగత ప్రయాణ గైడ్ సిద్ధంగా ఉంది! Google మ్యాప్స్‌లో అన్వేషించడానికి ఏదైనా ఐటెమ్‌పై క్లిక్ చేయండి.",
        "lang_name": "తెలుగు",
        "lang_select": "భాషను ఎంచుకోండి",
        "footer": "షేక్ ఇమ్రాన్ ద్వారా సృష్టించబడింది © 2025. అన్ని హక్కులు ప్రత్యేకించబడ్డాయి.",
        "download_button": "గైడ్‌ను .txtగా డౌన్‌లోడ్ చేయండి"
    },
    "kn": {
        "title": "ಟ್ರಿಪ್ ವಿಸ್ಪರರ್: ನಿಮ್ಮ AI ಪ್ರವಾಸ ಸಂಗಾತಿ ✈️",
        "placeholder": "ಉದಾ., ಪ್ಯಾರಿಸ್, ಟೋಕಿಯೋ, ನ್ಯೂಯಾರ್ಕ್",
        "button": "ಮಾರ್ಗದರ್ಶಿ ರಚಿಸಿ",
        "spinner": "{city_name} ಗಾಗಿ ಪ್ರವಾಸ ಮಾರ್ಗದರ್ಶಿಯನ್ನು ರಚಿಸಲಾಗುತ್ತಿದೆ... ✨",
        "weather_header": "{city_name} ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಹವಾಮಾನ:",
        "flights_button": "{city_name} ಗಾಗಿ ವಿಮಾನಗಳನ್ನು ಹುಡುಕಿ",
        "summary_header": "{city_name} ದ ಒಂದು ನೋಟ",
        "summary_error": "'{city_name}' ಗಾಗಿ ವಿಕಿಪೀಡಿಯಾ ಸಾರಾಂಶ ಕಂಡುಬಂದಿಲ್ಲ (ಭಾಷೆ: {lang_code}).",
        "guide_error": "ಮಾರ್ಗದರ್ಶಿ ರಚಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. AI ಮಾದರಿ ದೋಷ: {e}",
        "success": "ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಪ್ರವಾಸ ಮಾರ್ಗದರ್ಶಿ ಸಿದ್ಧವಾಗಿದೆ! Google ನಕ್ಷೆಗಳಲ್ಲಿ ಅನ್ವೇಷಿಸಲು ಯಾವುದೇ ಐಟಂ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "lang_name": "ಕನ್ನಡ",
        "lang_select": "ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "footer": "ಶೇಕ್ ಇಮ್ರಾನ್ ಅವರಿಂದ ರಚಿಸಲಾಗಿದೆ © 2025. ಎಲ್ಲಾ ಹಕ್ಕುಗಳನ್ನು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ.",
        "download_button": "ಮಾರ್ಗದರ್ಶಿಯನ್ನು .txt ಆಗಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ"
    },
    "ur": {
        "title": "ٹرپ وِسپرر: آپ کا AI سفری ساتھی ✈️",
        "placeholder": "مثلاً، پیرس، ٹوکیو، نیویارک",
        "button": "گائیڈ بنائیں",
        "spinner": "{city_name} کے لیے ٹریول گائیڈ تیار کی جا رہی ہے... ✨",
        "weather_header": "{city_name} میں موجودہ موسم:",
        "flights_button": "{city_name} کے لیے پروازیں تلاش کریں",
        "summary_header": "{city_name} کی ایک جھلک",
        "summary_error": "'{city_name}' کے لیے ویکیپیڈیا کا خلاصہ نہیں مل سکا (زبان: {lang_code})۔",
        "guide_error": "گائیڈ تیار نہیں ہو سکا۔ AI ماڈل کی خرابی: {e}",
        "success": "آپ کا ذاتی ٹریول گائیڈ تیار ہے! Google Maps پر اسے دریافت کرنے کے لیے کسی بھی آئٹم پر کلک کریں۔",
        "lang_name": "اردو",
        "lang_select": "زبان منتخب کریں۔",
        "footer": "شیخ عمران کا بنایا ہوا © 2025۔ جملہ حقوق محفوظ ہیں۔",
        "download_button": "گائیڈ کو .txt کے بطور ڈاؤن لوڈ کریں۔"
    }
}


# --- HELPER FUNCTIONS ---

# NEW: Added the Wikipedia image function back
def get_image_url(search_term, lang_code="en"):
    """
    Fetches the main image URL from a Wikipedia page.
    This will find landmarks, but likely not food items.
    """
    placeholder_url = "https://placehold.co/600x400/161B22/58A6FF?text=Image+Not+Found"
    try:
        wikipedia.set_lang(lang_code)
        # Use auto_suggest to find the best match (e.g., "Taj Mahal" from "taj mahal")
        page = wikipedia.page(search_term, auto_suggest=True)
        wikipedia.set_lang("en") # Reset language
        
        # Return the first image, or the placeholder if none found
        return page.images[0] if page.images else placeholder_url
            
    except Exception as e:
        print(f"Error getting Wikipedia image for '{search_term}': {e}") 
        wikipedia.set_lang("en") # Reset language on error
        return placeholder_url

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

def get_city_summary(city_name, lang_code, text_dict):
    """Fetches a concise summary of a city from Wikipedia in the specified language."""
    try:
        wikipedia.set_lang(lang_code) 
        summary = wikipedia.summary(city_name, sentences=3, auto_suggest=True)
        wikipedia.set_lang("en") # Reset to English for safety
        return summary
    except Exception:
        wikipedia.set_lang("en") 
        return text_dict["summary_error"].format(city_name=city_name, lang_code=lang_code)

def generate_travel_guide(city_name, lang_code, text_dict):
    """Uses Groq to generate a structured travel guide in the specified language."""
    
    lang_name = "English" 
    for code, texts in translations.items():
        if code == lang_code:
            lang_name = texts["lang_name"]
            break

    # NEW: Simplified prompt to only ask for Name and Description
    prompt = f"""
    Create a concise and exciting travel guide for "{city_name}".
    You MUST respond in this language: {lang_name} (language code: {lang_code}).
    
    You MUST provide two pieces of information for each item, separated by a pipe |.
    STRICTLY follow the format: 1. [Name] | [Description]
    Do not add any other text before or after the numbered lists.

    Example (if user requested 'Paris' and language 'en'):
    1. Eiffel Tower | A famous 19th-century iron lattice tower. It is one of the most recognizable structures in the world. Visitors can ride an elevator to the top for breathtaking views of the city.
    
    Here are the headings to use (translated to {lang_name}). Please provide 5 items for each category:
    ### Top 5 Tourist Attractions
    1. [Name] | [A brief, 3-sentence description]
    2. [Name] | [A brief, 3-sentence description]
    3. [Name] | [A brief, 3-sentence description]
    4. [Name] | [A brief, 3-sentence description]
    5. [Name] | [A brief, 3-sentence description]
    ### Top 5 Local Dishes to Try
    1. [Name] | [A brief, 3-sentence description]
    2. [Name] | [A brief, 3-sentence description]
    3. [Name] | [A brief, 3-sentence description]
    4. [Name] | [A brief, 3-sentence description]
    5. [Name] | [A brief, 3-sentence description]
    ### Top 5 Things to Avoid
    1. [Name] | [A brief, 3-sentence description]
    2. [Name] | [A brief, 3-sentence description]
    3. [Name] | [A brief, 3-sentence description]
    4. [Name] | [A brief, 3-sentence description]
    5. [Name] | [A brief, 3-sentence description]
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return text_dict["guide_error"].format(e=e)

# NEW: Simplified parser for the new prompt
def parse_guide_to_dict(guide_text):
    """Parses the raw text output from the AI into a structured dictionary."""
    guide_dict = {}
    sections = re.split(r'###\s*(.+)', guide_text)[1:]
    
    if not sections:
        print("Parser Error: No '###' sections found in AI response.")
        return {} 

    for i in range(0, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i].strip()
            content = sections[i+1].strip()
            items = []
            
            item_lines = re.findall(r"^\s*\d+\.\s*(.+)", content, re.MULTILINE)
            
            if not item_lines:
                 print(f"Parser Error: No numbered items found for section '{title}'.")
                 
            for item_line in item_lines:
                name, description = "", ""
                
                if '|' in item_line:
                    parts = item_line.split('|', 1) # Split into max 2 parts
                    name = parts[0].strip()
                    if len(parts) > 1:
                        description = parts[1].strip()
                else:
                    name = item_line.strip()
                    description = "..." # Add a placeholder if AI forgets
                
                if name:
                    items.append({"name": name, "description": description})
            
            if items:
                guide_dict[title] = items
    
    if not guide_dict:
         print(f"Parser Error: Final dictionary is empty. AI response was:\n{guide_text}")
         
    return guide_dict

def format_guide_for_download(guide_dict, city_name, lang_name):
    """Formats the guide dictionary into a clean string for .txt download."""
    download_text = f"Your Travel Guide for {city_name}\n"
    download_text += f"(Language: {lang_name})\n"
    download_text += "="*40 + "\n\n"
    
    for category, items in guide_dict.items():
        download_text += f"### {category}\n\n"
        for i, item in enumerate(items, 1):
            download_text += f"{i}. {item['name']}\n"
            download_text += f"   {item['description']}\n\n"
        download_text += "\n"
    
    return download_text

def generate_google_maps_link(item, city):
    """Generates a safe, encoded Google Maps link."""
    query = f"{item}, {city}"
    encoded_query = quote_plus(query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

# --- STREAMLIT UI ---

st.set_page_config(page_title="Trip Whisperer", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #0E117; }
    .block-container { max-width: 800px; padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3, p, .stMarkdown, .stTextInput>label { color: #FFFFFF; }
    h1 { text-align: center; }
    .stTextInput>div>div>input { border-radius: 15px; border: 1px solid #30363F; background-color: #0E117; color: #FFFFFF; padding: 12px; }
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

language_options = {texts["lang_name"]: code for code, texts in translations.items()}
selected_language_name = st.selectbox(
    label=translations["en"]["lang_select"], # Label is always in English
    options=language_options.keys(),
    index=0 
)
selected_lang_code = language_options[selected_language_name]

ui_texts = translations[selected_lang_code]

st.title(ui_texts["title"])

city_input = st.text_input(
    "Enter a city name:", 
    label_visibility="collapsed", 
    placeholder=ui_texts["placeholder"]
)

if st.button(ui_texts["button"]) and city_input:
    
    cleaned_city_name = city_input.strip().strip(string.punctuation)
    
    with st.spinner(ui_texts["spinner"].format(city_name=cleaned_city_name)):
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        weather_info = get_weather_info(cleaned_city_name, WEATHER_API_KEY)
        st.markdown(f"**{ui_texts['weather_header'].format(city_name=cleaned_city_name.title())}**")
        st.write(weather_info)
        
        flight_link = generate_flight_search_link(cleaned_city_name)
        st.markdown(f"<a href='{flight_link}' target='_blank' style='display:inline-block; margin-top:10px; padding:8px 16px; background-color:#2563EB; color:white; border-radius:10px; text-decoration:none;'>{ui_texts['flights_button'].format(city_name=cleaned_city_name.title())}</a>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True) 
        st.subheader(ui_texts["summary_header"].format(city_name=cleaned_city_name.title()))
        summary = get_city_summary(cleaned_city_name, selected_lang_code, ui_texts)
        st.write(summary)
        st.markdown("</div>", unsafe_allow_html=True)

        guide_text = generate_travel_guide(cleaned_city_name, selected_lang_code, ui_texts)
        
        if "Could not generate guide" in guide_text:
            st.error(guide_text)
        else:
            parsed_guide = parse_guide_to_dict(guide_text)
            
            if not parsed_guide:
                st.error("The AI returned an invalid format. Please try again.")
            else:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                for category, items in parsed_guide.items():
                    st.subheader(category)
                    for item in items:
                        
                        col1, col2 = st.columns([1, 2]) 
                        
                        with col1:
                            # NEW: Get image from Wikipedia
                            image_url = get_image_url(item["name"], selected_lang_code)
                            st.image(image_url, caption=f"{item['name']}", use_container_width=True)
                        
                        with col2:
                            map_link = generate_google_maps_link(item["name"], cleaned_city_name)
                            st.markdown(f"#### [{item['name']}]({map_link})")
                            st.write(item["description"])
                            
                        st.divider() 
                        
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.success(ui_texts["success"])
                
                st.markdown("---")
                
                download_text = format_guide_for_download(parsed_guide, cleaned_city_name, selected_language_name)
                
                st.download_button(
                    label=ui_texts["download_button"],
                    data=download_text,
                    file_name=f"{cleaned_city_name}_guide.txt",
                    mime="text/plain",
                    use_container_width=True
                )

# --- Footer ---
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #888; font-size: 0.9rem;'>{ui_texts['footer']}</div>", unsafe_allow_html=True)


