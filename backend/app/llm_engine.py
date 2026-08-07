import os
import re
import httpx
from typing import List, Tuple
from .models import HistoricalTicket
from .utils.error_handler import LLMEngineError, RateLimitError, retry_on_error

class LLMEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "llama-3.1-8b-instant"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    @retry_on_error(max_retries=3, backoff=2.0, exception_types=(httpx.RequestError, LLMEngineError, RateLimitError))
    async def generate_resolutions(
        self, 
        ticket_description: str, 
        similar_tickets: List[Tuple[HistoricalTicket, float]]
    ) -> List[str]:
        """Generate exactly 5 actionable resolution points using Groq LLM"""
        
        # Build context from similar tickets
        context = self._build_context(similar_tickets)
        
        prompt = f"""You are an IT support expert. Based on the following ticket and similar historical cases, provide EXACTLY 5 clear, actionable resolution steps.

Current Ticket:
{ticket_description}

Similar Historical Cases:
{context}

Requirements:
- Provide EXACTLY 5 numbered resolution steps
- Each step must be specific and actionable
- Steps should be ordered from most likely to resolve the issue to least likely
- Keep each step concise (1-2 sentences)
- Focus on practical solutions, not theory

Format your response as:
1. [First resolution step]
2. [Second resolution step]
3. [Third resolution step]
4. [Fourth resolution step]
5. [Fifth resolution step]
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9
        }
        
        try:
            if self.api_key == "gsk_your_api_key_here" or not self.api_key:
                raise LLMEngineError("No API key provided")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            resolutions = self._parse_resolutions(content)
            
            # Ensure exactly 5 resolutions
            if len(resolutions) != 5:
                raise LLMEngineError(f"Expected 5 resolutions, got {len(resolutions)}")
            
            return resolutions
            
        except Exception as e:
            # Context-Aware Offline Fallback
            fallback = []
            for ticket, _ in similar_tickets:
                if ticket.resolution_text and ticket.resolution_text not in fallback:
                    fallback.append(ticket.resolution_text)
                if len(fallback) == 5:
                    break
                    
            generic = [
                "Restart the device to clear memory and reload drivers.",
                "Check for system or software updates and install them.",
                "Verify network connection and reset the router if necessary.",
                "Clear application cache or browser history.",
                "Contact higher tier IT support if the problem persists."
            ]
            
            for g in generic:
                if len(fallback) == 5:
                    break
                if g not in fallback:
                    fallback.append(g)
                    
            return fallback[:5]
    
    def _build_context(self, similar_tickets: List[Tuple[HistoricalTicket, float]]) -> str:
        """Build context string from similar tickets"""
        context_parts = []
        for ticket, score in similar_tickets:
            context_parts.append(
                f"- Issue: {ticket.title}\n"
                f"  Description: {ticket.description}\n"
                f"  Resolution: {ticket.resolution_text}\n"
                f"  Similarity: {score:.2f}\n"
            )
        return "\n".join(context_parts)
    
    def _parse_resolutions(self, content: str) -> List[str]:
        """Parse LLM response into list of 5 resolutions"""
        lines = content.strip().split("\n")
        resolutions = []
        
        for line in lines:
            line = line.strip()
            # Match numbered lines: "1. ", "1) ", "1 - ", etc.
            if re.match(r"^\d+[\.\)\-\:]\s+", line):
                resolution = re.sub(r"^\d+[\.\)\-\:]\s+", "", line)
                resolutions.append(resolution)
        
        return resolutions
