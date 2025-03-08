import json
import openai

# Load OpenAI API key from config
with open("config.json") as f:
    config = json.load(f)
    openai.api_key = config["openai_api_key"]

def fetch_conjugation(verb, tense):
    """Queries OpenAI API to fetch conjugations and Russian translations for given verb and tense."""
    client = openai.OpenAI(api_key=config["openai_api_key"])
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": f"Return only a JSON object without any explanation. The object should contain the conjugations of '{verb}' in French in {tense} for Je, Tu, Il/Elle, Nous, Vous, Ils/Elles, along with the Russian translation for infinive form under 'translation_ru'. The format must be: {{ 'Je': '', 'Tu': '', 'Il/Elle': '', 'Nous': '', 'Vous': '', 'Ils/Elles': '', 'translation_ru': '' }}"}]
    )
    
    raw_content = response.choices[0].message.content.strip().strip('```json').strip('```')
    print("Raw API Response:", raw_content)  # Debugging output
    
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response from OpenAI API.")
        return {}
    
    conjugations = {row[2]: row[3] for row in result}  # Mapping pronoun -> conjugation
    conjugations["translation_ru"] = result[0][4]  # Adding Russian translation
    return conjugations