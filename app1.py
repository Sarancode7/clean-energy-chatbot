from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model with better system prompt
system_prompt = """
You are an AI assistant specialized in renewable energy topics. Provide accurate, helpful information about:
- Solar energy and solar panels
- Wind power and turbines
- Geothermal energy
- Hydroelectric power
- Other renewable energy sources
- Environmental benefits of clean energy
- Costs and economic considerations
- Government incentives and subsidies
- Energy efficiency recommendations

IMPORTANT FORMATTING INSTRUCTIONS:
1. Keep responses concise and focused - aim for 3-5 short bullet points when possible
2. For complex topics, provide a brief introduction followed by bullet points
3. Use asterisks for bullet points: "* Key point here"
4. Use double asterisks for emphasis: "**Important term**"
5. Avoid lengthy explanations - focus on key information only

Keep responses focused on these topics. If asked about unrelated topics, politely redirect the conversation
to renewable energy. Provide personalized advice when given specific information about location, budget, or needs.
"""

# Load the model with the specialized system prompt
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=system_prompt
)

# Start chat session with history
chat_session = model.start_chat(history=[])

# Define keywords for allowed topics (expanded list)
ALLOWED_KEYWORDS = [
    # Energy sources
    "solar", "wind", "geothermal", "hydro", "hydroelectric", "tidal", "biomass", 
    "renewable", "clean energy", "green energy", "sustainable energy",
    
    # Equipment
    "solar panel", "wind turbine", "heat pump", "battery storage", "energy storage",
    
    # Benefits and considerations
    "carbon", "emission", "climate", "greenhouse gas", "environmental", "sustainable",
    "efficiency", "cost", "savings", "roi", "return on investment", "payback",
    
    # Policy and incentives
    "subsidy", "subsidies", "tax credit", "incentive", "rebate", "policy", "grant",
    
    # Installation and usage
    "install", "installation", "home energy", "grid", "off-grid", "net metering",
    "power", "electricity", "generation", "consumption", "usage", "kwh", "kilowatt",
    
    # Recommendations and comparison
    "recommend", "comparison", "versus", "vs", "better", "best", "option", "alternative"
]

# Expanded greetings detection
GREETING_PATTERNS = [
    r'\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day))\b',
    r'\bhow\s+(are|is|was)\s+(you|it|things)\b',
    r'\bnice\s+to\s+(meet|see)\s+you\b',
    r'\bwelcome\b'
]

def is_greeting(user_input):
    """Check if user input contains a greeting using regex patterns."""
    user_input = user_input.lower()
    return any(re.search(pattern, user_input) for pattern in GREETING_PATTERNS)

def is_related_to_energy(user_input):
    """Check if the user input contains words related to clean energy topics."""
    user_input = user_input.lower()
    return any(keyword in user_input for keyword in ALLOWED_KEYWORDS)

def get_location_info(user_input):
    """Extract potential location information for more personalized responses."""
    # This is a simple placeholder - in a real app, you might use NER or a more sophisticated approach
    location_patterns = [
        r'in\s+([A-Za-z\s]+)', 
        r'live\s+in\s+([A-Za-z\s]+)',
        r'from\s+([A-Za-z\s]+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, user_input)
        if match:
            return match.group(1).strip()
    return None

@app.route('/')
def home():
    return render_template('index.html')

# Add this to your app.py file, replacing the existing off-topic handling

def get_off_topic_response(user_message):
    """Generate a varied, natural-sounding response to redirect conversation to energy topics."""
    
    # Extract any potential topic from the user's message
    words = user_message.lower().split()
    nouns = [word for word in words if len(word) > 3 and word not in ['about', 'what', 'know', 'tell', 'does', 'like', 'with']]
    
    # List of varied responses with placeholders for personalization
    responses = [
        "I don't have information about {topic}, as I'm specialized in renewable energy. Is there something about solar, wind, or other clean energy sources I can help with?",
        
        "While I can't tell you about {topic}, I'd be happy to discuss renewable energy topics like solar panels, wind turbines, or energy efficiency. What would you like to know?",
        
        "I'm actually designed to focus on clean energy topics rather than {topic}. Would you like to learn about renewable energy technologies instead?",
        
        "I'm sorry, but I'm specifically programmed to discuss renewable energy, not {topic}. I can tell you about solar, wind, or geothermal energy if you're interested.",
        
        "Rather than {topic}, my expertise is in renewable energy solutions. I can help with questions about energy costs, environmental benefits, or installation options. What interests you?",
        
        "I don't have information about {topic}. However, I can share insights about renewable energy technologies, costs, and benefits. Would that be helpful?",
        
        "I'm designed to assist with clean energy topics rather than {topic}. Would you like to explore solar power, wind energy, or perhaps energy efficiency options?"
    ]
    
    import random
    
    # Choose a random response
    response = random.choice(responses)
    
    # If we found a likely topic in the message, use it
    if nouns:
        topic_word = nouns[0]
        return response.format(topic=topic_word)
    else:
        # General fallback if we can't identify a specific topic
        return response.format(topic="that topic")
# Keywords to identify subsidy-related queries
SUBSIDY_KEYWORDS = [
    "subsidy", "subsidies", "tax credit", "incentive", "rebate", "financial assistance",
    "government program", "central scheme", "state scheme", "grant", "funding", "yojana"
]

def is_subsidy_question(user_message):
    """Determine if the user is asking about subsidies or incentives."""
    user_message = user_message.lower()
    return any(keyword in user_message for keyword in SUBSIDY_KEYWORDS)

def enhance_subsidy_prompt(user_message):
    """
    Create an enhanced prompt for Gemini to better handle subsidy questions
    specifically for Indian government schemes.
    """
    enhanced_prompt = f"""
{user_message}

IMPORTANT: The user is asking about renewable energy subsidies or incentives in India. In your response:
1. Identify the specific Indian government scheme or program name related to their question
2. Provide a brief description of the incentive (eligibility, benefits, etc.)
3. Do NOT include any external website links
4. Format your response without using asterisks (*) in headings
5. Focus ONLY on Indian government subsidies and schemes, not U.S. or other countries
6. Mention the specific ministry or department responsible for the scheme

For example: "PM-KUSUM Scheme: Implemented by the Ministry of New and Renewable Energy to promote solar energy in agriculture."

If discussing solar incentives, mention schemes like "Rooftop Solar Programme" or "MNRE Subsidies for Solar Projects."
"""
    return enhanced_prompt

# Modify your format_long_response function to remove asterisks from headings
def format_long_response(response_text):
    """
    Format lengthy responses for better readability by:
    1. Converting markdown-style bullet points into proper HTML list items
    2. Properly handling bold text with ** markers
    3. Making responses more concise
    4. Removing asterisks from headings
    """
    
    # Remove asterisks from headings if present
    response_text = re.sub(r'\*\s+([\w\s]+):', r'\1:', response_text)
    
    # First, convert all bold text markers
    response_text = response_text.replace('**', '<strong>', 1)
    while '**' in response_text:
        response_text = response_text.replace('**', '</strong>', 1)
        if '**' in response_text:
            response_text = response_text.replace('**', '<strong>', 1)
    
    # Limit response length for suggestion chips (when responding to preset questions)
    if len(response_text) > 800:
        # Look for natural breakpoints
        breakpoints = [
            "\n\nIf you'd like to know more",
            "\n\nFor more information",
            "\n\nTo learn more",
            "\n\nAdditional factors",
            "\n\nOther considerations",
            "\n\nIn conclusion",
            "\n\nFurthermore",
        ]
        
        for breakpoint in breakpoints:
            if breakpoint in response_text:
                response_text = response_text.split(breakpoint)[0]
                response_text += "\n\n<em>Click for more detailed information.</em>"
                break
        
        # If no natural breakpoint found and text is still long, truncate to key points
        if len(response_text) > 800:
            # Check if there are bullet points
            if "\n* " in response_text or "\n- " in response_text:
                # Extract intro paragraph and first few bullet points
                lines = response_text.split("\n")
                intro_text = []
                bullet_points = []
                
                for line in lines:
                    if line.strip().startswith("* ") or line.strip().startswith("- "):
                        bullet_points.append(line)
                    elif not bullet_points:  # Still in intro
                        intro_text.append(line)
                
                # Keep intro and at most 4-5 bullet points
                max_bullets = min(5, len(bullet_points))
                response_text = "\n".join(intro_text) + "\n" + "\n".join(bullet_points[:max_bullets])
                response_text += "\n\n<em>Ask me for further more information.</em>"
    
    # Handle single asterisk bullet points (markdown style)
    if "\n* " in response_text or "\n- " in response_text:
        # Split the text into lines
        lines = response_text.split("\n")
        formatted_text = ""
        in_list = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this line is a bullet point
            if line_stripped.startswith("* ") or line_stripped.startswith("- "):
                # Start a list if we're not in one
                if not in_list:
                    formatted_text += "<ul class='response-list'>"
                    in_list = True
                
                # Add the bullet point as a list item (remove the asterisk/dash)
                item_content = line_stripped[2:].strip()
                formatted_text += f"<li>{item_content}</li>"
            else:
                # Close the list if we were in one
                if in_list:
                    formatted_text += "</ul>"
                    in_list = False
                
                # Add the line as regular text
                if line_stripped:
                    formatted_text += f"{line}\n"
        
        # Close any open list
        if in_list:
            formatted_text += "</ul>"
        
        return formatted_text
    
    # Handle triple asterisk sections as before
    elif "***" in response_text:
        # Split by triple asterisk sections
        sections = response_text.split("***")
        
        formatted_text = sections[0]  # Keep the intro text
        
        # Start a list for the remaining sections
        formatted_text += "<ul class='response-list'>"
        
        for section in sections[1:]:
            if ":" in section:
                # Extract the title part (before the colon)
                parts = section.split(":", 1)
                title = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""
                
                # Create a list item with bold title
                formatted_text += f"<li><strong>{title}:</strong> {content}</li>"
            else:
                # Just add as a regular list item if no colon
                formatted_text += f"<li>{section.strip()}</li>"
        
        formatted_text += "</ul>"
        return formatted_text
    
    # Look for numbered lists (1., 2., etc.)
    elif any(line.strip().startswith(f"{i}.") for i in range(1, 10) for line in response_text.split("\n")):
        lines = response_text.split("\n")
        formatted_lines = []
        in_list = False
        
        for line in lines:
            # Check if this line starts a numbered item
            if any(line.strip().startswith(f"{i}.") for i in range(1, 10)):
                if not in_list:
                    formatted_lines.append("<ol class='response-list'>")
                    in_list = True
                formatted_lines.append(f"<li>{line.strip()[2:].strip()}</li>")
            else:
                if in_list and line.strip():
                    # This is part of the previous list item
                    formatted_lines[-1] = formatted_lines[-1][:-5] + " " + line.strip() + "</li>"
                elif in_list and not line.strip():
                    # End of list
                    formatted_lines.append("</ol>")
                    in_list = False
                    if line.strip():
                        formatted_lines.append(line)
                else:
                    # Regular paragraph
                    formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append("</ol>")
            
        return "\n".join(formatted_lines)
    
    # Default formatting - add paragraph breaks
    else:
        paragraphs = [p for p in response_text.split("\n\n") if p.strip()]
        return "<p>" + "</p><p>".join(paragraphs) + "</p>"

# Modify your @app.route('/chat') function to include this logic:


@app.route('/chat', methods=['POST'])
def chat_response():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        # If empty message, prompt for a question
        if not user_message:
            return jsonify({
                'response': "Please ask a question about renewable energy."
            })
        
        # Handle greetings with energy-focused response
        if is_greeting(user_message) and len(user_message.split()) < 5:
            greeting_responses = [
                "Hello! I'm your renewable energy assistant. How can I help you with clean energy today?",
                "Hi there! I'm here to answer your questions about solar, wind, and other renewable energy sources. What would you like to know?",
                "Greetings! I specialize in renewable energy information. What clean energy topic are you interested in?"
            ]
            import random
            return jsonify({'response': random.choice(greeting_responses)})
        
        # Check if message is related to energy
        if is_related_to_energy(user_message):
            # Handle subsidy questions with special prompt enhancement
            if is_subsidy_question(user_message):
                enhanced_prompt = enhance_subsidy_prompt(user_message)
            else:
                # Try to extract location for more personalized response
                location = get_location_info(user_message)
                
                # Add location context if found
                context_message = user_message
                if location:
                    context_message += f"\n\nPlease provide information specific to {location} if relevant."
                    
                enhanced_prompt = context_message + "\n\nFor lengthy responses, please structure your answer with clear headings and bullet points for better readability."
            
            # Send to Gemini
            response = chat_session.send_message(enhanced_prompt)
            
            # Format the response for better readability
            formatted_response = format_long_response(response.text)
            
            return jsonify({'response': formatted_response})
        else:
            # Generate a varied, personalized off-topic response
            return jsonify({
                'response': get_off_topic_response(user_message)
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'response': "I'm having trouble processing your request. Please try again with a question about renewable energy."
        })

if __name__ == '__main__':
    app.run(debug=True)