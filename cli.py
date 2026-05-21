import click
import os
import json
from core.parser import GraphifyHeuristicParser
from core.synthesizer import PromptSynthesizer

@click.group()
def main():
    """
    🚀 PromptGrapher: Global Context-Aware AI Rules Generator.
    Extracts codebase structural DNA via Graphify and dynamically builds .cursorrules.
    """
    pass

@main.command()
def init():
    """Initializes global environment configuration parameters for the AI engine."""
    env_content = """# PromptGrapher AI Engine Configurations
AI_BASE_URL="https://api.groq.com/openai/v1"
AI_API_KEY="ENTER_YOUR_GROQ_API_KEY_HERE"
AI_MODEL_NAME="llama-3.3-70b-versatile"
"""
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        click.echo(click.style("✨ Template .env file successfully created! Please update your API credentials inside it.", fg="green", bold=True))
    else:
        click.echo(click.style("⚠️ Configuration file .env already exists in this root directory.", fg="yellow"))

@main.command()
@click.argument('path', default='.')
@click.option('--model', default=None, help='Target LLM model override (defaults to .env value)')
def analyze(path, model):
    """Parses Graphify manifest and drops .cursorrules directly into target folder."""
    click.echo(click.style("\n🚀 [PromptGrapher] Starting codebase architectural analysis...", fg="cyan", bold=True))
    
    # Target path aur manifest route verify karna
    project_path = os.path.abspath(path)
    manifest_path = os.path.join(project_path, "graphify-out", "manifest.json")
    
    if not os.path.exists(manifest_path):
        click.echo(click.style(f"❌ Error: Graphify output missing at '{manifest_path}'", fg="red", bold=True))
        click.echo(click.style("👉 Tip: Run 'graphify extract <path>' first inside this directory.", fg="yellow"))
        return

    try:
        # Phase 1: AST Metadata Extraction
        click.echo("[*] Parsing Graphify structural dependencies...")
        parser = GraphifyHeuristicParser(manifest_path)
        dna_metrics = parser.compile_heuristics_payload()
        
        click.echo(click.style("📊 Architectural metrics successfully extracted:", fg="green"))
        click.echo(json.dumps(dna_metrics, indent=2))
        
        # Phase 2: Orchestrate Enterprise LLM Prompt Synthesis
        click.echo("\n[*] Contacting AI Cognitive Synthesis Engine...")
        synthesizer = PromptSynthesizer()
        
        # Runtime parameters dynamic model override condition
        if model:
            synthesizer.model_name = model
            
        generated_rules_path = synthesizer.generate_rules(dna_metrics, output_path=project_path)
        
        click.echo(click.style(f"\n🎉 [Success] Architectural lockdown complete!", fg="green", bold=True))
        click.echo(click.style(f"🎯 Rulebook successfully activated at: {generated_rules_path}\n", fg="yellow"))
        
    except ValueError as ve:
        click.echo(click.style(f"❌ Configuration Error: {ve}", fg="red", bold=True))
        click.echo(click.style("👉 Please verify your local '.env' file parameters.", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"💥 Pipeline Execution Halted: {e}", fg="red", bold=True))

if __name__ == '__main__':
    main()