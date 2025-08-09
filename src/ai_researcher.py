import logging
import requests
from typing import List, Optional
import json

class AIResearcher:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.anthropic_available = bool(api_key)
        
        if self.anthropic_available:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                logging.warning("Anthropic library not installed, using fallback methods")
                self.anthropic_available = False
    
    def research_answer(self, question: str, options: List[dict], context: str) -> Optional[str]:
        try:
            if self.anthropic_available:
                answer = self.query_anthropic(question, options, context)
                if answer:
                    return answer
            
            answer = self.search_web_api(question, context)
            if answer:
                return answer
            
            return self.use_local_heuristics(question, options)
        
        except Exception as e:
            logging.error(f"AI research error: {e}")
            return None
    
    def query_anthropic(self, question: str, options: List[dict], context: str) -> Optional[str]:
        try:
            options_text = "\n".join([f"{i+1}. {opt['text']}" for i, opt in enumerate(options)])
            
            prompt = f"""Context: {context}
            
Question: {question}

Options:
{options_text if options_text else "No options provided (short answer expected)"}

Please provide only the correct answer. For multiple choice, respond with just the letter or number. For short answer, provide a brief response."""
            
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            answer = message.content[0].text.strip()
            logging.info(f"AI response: {answer}")
            
            return answer
        
        except Exception as e:
            logging.error(f"Anthropic API error: {e}")
            return None
    
    def search_web_api(self, question: str, context: str) -> Optional[str]:
        try:
            search_query = f"{context} {question}"
            
            wiki_answer = self.search_wikipedia(search_query)
            if wiki_answer:
                return wiki_answer
            
            return None
        
        except Exception as e:
            logging.error(f"Web search error: {e}")
            return None
    
    def search_wikipedia(self, query: str) -> Optional[str]:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data['query']['search']:
                page_title = data['query']['search'][0]['title']
                
                extract_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'exsentences': 3
                }
                
                extract_response = requests.get(url, params=extract_params, timeout=5)
                extract_data = extract_response.json()
                
                pages = extract_data['query']['pages']
                for page_id in pages:
                    if 'extract' in pages[page_id]:
                        return self.extract_answer_from_text(
                            pages[page_id]['extract'], 
                            query
                        )
            
            return None
        
        except Exception as e:
            logging.error(f"Wikipedia search error: {e}")
            return None
    
    def extract_answer_from_text(self, text: str, question: str) -> str:
        keywords = question.lower().split()
        
        sentences = text.split('.')
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            score = sum(1 for keyword in keywords if keyword in sentence.lower())
            if score > best_score:
                best_score = score
                best_sentence = sentence.strip()
        
        if best_sentence:
            words = best_sentence.split()
            if len(words) > 10:
                return ' '.join(words[:10])
            return best_sentence
        
        return ""
    
    def use_local_heuristics(self, question: str, options: List[dict]) -> Optional[str]:
        question_lower = question.lower()
        
        if 'not' in question_lower or 'false' in question_lower:
            if options and len(options) > 2:
                return options[-1]['text'][0]
        
        if 'all of the above' in ' '.join([opt['text'].lower() for opt in options]):
            for opt in options:
                if 'all of the above' in opt['text'].lower():
                    return opt['text'][0]
        
        if 'year' in question_lower:
            for opt in options:
                if any(char.isdigit() for char in opt['text']):
                    return opt['text'][0]
        
        if options and len(options) > 2:
            middle_index = len(options) // 2
            return options[middle_index]['text'][0]
        
        return "Unable to determine" if not options else options[0]['text'][0]