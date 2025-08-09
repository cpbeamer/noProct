from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.logger import get_logger
from src.core.exceptions import APIError

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Query the AI provider for an answer"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = get_logger("AnthropicProvider")
        self.client = None
        
        if api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                self.logger.warning("Anthropic library not installed")
    
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Query Anthropic Claude for answer"""
        if not self.client:
            return None
        
        try:
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            
            prompt = f"""Context: {context}
            
Question: {question}

Options:
{options_text if options_text else "No options provided (short answer expected)"}

Provide only the correct answer. For multiple choice, respond with just the letter or number. 
For short answer, provide a brief, direct response."""
            
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = message.content[0].text.strip()
            self.logger.info(f"Anthropic response: {answer[:50]}...")
            return answer
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available"""
        return self.client is not None

class OpenAIProvider(AIProvider):
    """OpenAI GPT API provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = get_logger("OpenAIProvider")
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Query OpenAI GPT for answer"""
        if not self.api_key:
            return None
        
        try:
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": f"Context: {context}"},
                    {"role": "user", "content": f"Question: {question}\n\nOptions:\n{options_text}\n\nProvide only the answer."}
                ],
                "temperature": 0,
                "max_tokens": 100
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            answer = response.json()['choices'][0]['message']['content'].strip()
            self.logger.info(f"OpenAI response: {answer[:50]}...")
            return answer
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return bool(self.api_key)

class LocalProvider(AIProvider):
    """Local heuristic-based provider"""
    
    def __init__(self):
        self.logger = get_logger("LocalProvider")
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict:
        """Load local knowledge base"""
        try:
            with open('data/knowledge_base.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Use local heuristics to answer"""
        question_lower = question.lower()
        
        # Check knowledge base
        for key, value in self.knowledge_base.items():
            if key.lower() in question_lower:
                return value
        
        # Heuristic strategies
        if options:
            # Look for "all of the above"
            for opt in options:
                if 'all of the above' in opt.lower():
                    return opt[0] if len(opt) > 0 else opt
            
            # Look for negatives
            if 'not' in question_lower or 'false' in question_lower:
                # Often the last option
                return options[-1][0] if options and len(options[-1]) > 0 else options[-1]
            
            # Default to middle option
            if len(options) >= 3:
                return options[len(options) // 2][0] if len(options[len(options) // 2]) > 0 else options[len(options) // 2]
        
        return "Unable to determine"
    
    def is_available(self) -> bool:
        """Local provider is always available"""
        return True

class WebSearchProvider(AIProvider):
    """Web search based provider"""
    
    def __init__(self):
        self.logger = get_logger("WebSearchProvider")
    
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Search web for answer"""
        try:
            # Search Wikipedia
            wiki_answer = self._search_wikipedia(f"{context} {question}")
            if wiki_answer:
                return self._match_to_options(wiki_answer, options)
            
            # Search DuckDuckGo (no API key required)
            ddg_answer = self._search_duckduckgo(f"{context} {question}")
            if ddg_answer:
                return self._match_to_options(ddg_answer, options)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Web search error: {e}")
            return None
    
    def _search_wikipedia(self, query: str) -> Optional[str]:
        """Search Wikipedia API"""
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
                
                # Get page extract
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
                        return pages[page_id]['extract']
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Wikipedia search failed: {e}")
            return None
    
    def _search_duckduckgo(self, query: str) -> Optional[str]:
        """Search DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            # Check for instant answer
            if data.get('AbstractText'):
                return data['AbstractText']
            elif data.get('Answer'):
                return data['Answer']
            
            return None
            
        except Exception as e:
            self.logger.debug(f"DuckDuckGo search failed: {e}")
            return None
    
    def _match_to_options(self, text: str, options: List[str]) -> str:
        """Match search result to provided options"""
        if not options:
            # Return first sentence for short answer
            sentences = text.split('.')
            return sentences[0] if sentences else text[:100]
        
        # Find best matching option
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for option in options:
            option_words = option.lower().split()
            score = sum(1 for word in option_words if word in text_lower)
            if score > best_score:
                best_score = score
                best_match = option
        
        if best_match:
            return best_match[0] if len(best_match) > 0 else best_match
        
        return options[0][0] if options and len(options[0]) > 0 else options[0]
    
    def is_available(self) -> bool:
        """Web search is available if internet connection exists"""
        try:
            requests.get("https://www.google.com", timeout=2)
            return True
        except:
            return False

class EnhancedAIResearcher:
    """Enhanced AI researcher with multiple providers and fallback"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = get_logger("AIResearcher")
        
        # Initialize providers
        self.providers = []
        
        # Add configured providers
        if config.get('api_key'):
            self.providers.append(AnthropicProvider(config['api_key']))
        
        if config.get('openai_api_key'):
            self.providers.append(OpenAIProvider(config['openai_api_key']))
        
        # Always add fallback providers
        self.providers.append(WebSearchProvider())
        self.providers.append(LocalProvider())
        
        # Cache for answers
        self.answer_cache = {}
        self.cache_size = 100
    
    def research_answer(self, question: str, options: List[Dict], 
                       context: str) -> Optional[str]:
        """Research answer using multiple providers"""
        # Check cache
        cache_key = self._generate_cache_key(question, options)
        if cache_key in self.answer_cache:
            self.logger.debug("Answer retrieved from cache")
            return self.answer_cache[cache_key]
        
        # Extract option texts
        option_texts = [opt.get('text', '') for opt in options] if options else []
        
        # Try providers in parallel for speed
        answer = self._query_providers_parallel(question, context, option_texts)
        
        if not answer:
            # Fallback to sequential with all providers
            answer = self._query_providers_sequential(question, context, option_texts)
        
        # Cache answer
        if answer:
            self._cache_answer(cache_key, answer)
        
        return answer
    
    def _query_providers_parallel(self, question: str, context: str, 
                                 options: List[str]) -> Optional[str]:
        """Query available providers in parallel"""
        available_providers = [p for p in self.providers if p.is_available()]
        
        if not available_providers:
            return None
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(p.query, question, context, options): p 
                for p in available_providers[:3]  # Limit parallel queries
            }
            
            for future in as_completed(futures, timeout=10):
                try:
                    answer = future.result()
                    if answer:
                        provider = futures[future]
                        self.logger.info(f"Answer from {provider.__class__.__name__}")
                        return answer
                except Exception as e:
                    self.logger.debug(f"Provider failed: {e}")
        
        return None
    
    def _query_providers_sequential(self, question: str, context: str, 
                                   options: List[str]) -> Optional[str]:
        """Query providers sequentially as fallback"""
        for provider in self.providers:
            if provider.is_available():
                try:
                    answer = provider.query(question, context, options)
                    if answer:
                        self.logger.info(f"Answer from {provider.__class__.__name__} (fallback)")
                        return answer
                except Exception as e:
                    self.logger.debug(f"Provider {provider.__class__.__name__} failed: {e}")
        
        return None
    
    def _generate_cache_key(self, question: str, options: List[Dict]) -> str:
        """Generate cache key for question"""
        import hashlib
        
        key_parts = [question]
        if options:
            key_parts.extend([opt.get('text', '') for opt in options])
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _cache_answer(self, key: str, answer: str):
        """Cache answer with size limit"""
        self.answer_cache[key] = answer
        
        # Maintain cache size
        if len(self.answer_cache) > self.cache_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self.answer_cache))
            del self.answer_cache[oldest_key]
    
    def add_provider(self, provider: AIProvider):
        """Add a new AI provider"""
        self.providers.insert(0, provider)  # Add at beginning for priority
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get availability status of all providers"""
        return {
            provider.__class__.__name__: provider.is_available()
            for provider in self.providers
        }