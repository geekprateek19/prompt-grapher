import os
from openai import OpenAI
from dotenv import load_dotenv

class PromptSynthesizer:
    def __init__(self):
        # Local system context `.env` file reading trigger
        load_dotenv()
        
        # Pull configurations from environment parameters dynamically
        self.base_url = os.environ.get("AI_BASE_URL")
        self.api_key = os.environ.get("AI_API_KEY")
        self.model_name = os.environ.get("AI_MODEL_NAME")
        
        if not self.api_key:
            raise ValueError("Configuration Error: 'AI_API_KEY' environment property is missing.")
        if not self.model_name:
            raise ValueError("Configuration Error: 'AI_MODEL_NAME' designation property is missing.")
            
        # Initializing the unified OpenAI API client engine interface
        # Works out-of-the-box for Groq, OpenRouter, DeepSeek, Local Ollama, etc.
        self.client = OpenAI(
            base_url=self.base_url, # Will fall back to standard OpenAI endpoint if None
            api_key=self.api_key
        )

    def generate_rules(self, dna_metrics, output_path):
        prompt = f"""
        You are a Meta-Prompt Engineer and Elite Enterprise Software Architect.
        Analyze this exact structural DNA extracted from a target codebase via Abstract Syntax Tree (AST) graph data:
        - Architecture Implemented: {dna_metrics.get('architecture_type')}
        - Code Naming System: {dna_metrics.get('naming_pattern')}
        - High-Risk Files/God Classes: {dna_metrics.get('god_classes')}

        Task: Generate a rigorous, flawless, and direct `.cursorrules` configuration file for this repository.

        CRITICAL INSTRUCTIONS FOR PROMPT GENERATION:
        1. DO NOT use descriptive words like "AI tool ko instruct karna chahiye" or "should be done".
        2. Use STRICT, DIRECT, and AGGRESSIVE commands (e.g., "Always use...", "Strictly enforce...", "Never rewrite...").
        3. Include explicit sections: [ROLE], [ARCHITECTURE RULES], [PERFORMANCE HYGIENE], [DATA SAFETY], [COMMUNICATION STYLE].
        4. Enforce the Hinglish rule explicitly: "Explanations must be in Hinglish, but code must be professional C# English."
        5. Output RAW markdown configuration only. Do not wrap the final output inside backticks (```markdown).
        """

        try:
            # Agnostic chat completions matrix triggering across connected adapters
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            rules_file_path = os.path.join(output_path, ".cursorrules")
            with open(rules_file_path, "w", encoding="utf-8") as f:
                f.write(response.choices[0].message.content)
                
            return rules_file_path
        except Exception as e:
            raise RuntimeError(f"Unified AI Engine Pipeline processing failure: {e}")