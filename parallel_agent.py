# parallel_agent.py
#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "openai-agents>=0.0.2",
#   "rich>=13.7.0", # For console output
# ]
# ///

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

# Assuming openai-agents handles the client import internally based on basic_agent.py
from agents import Agent, Runner 
from openai import OpenAIError # For specific error handling

# Initialize console
console = Console()

# Function to create the agent
def create_basic_agent(model: str, instructions: Optional[str] = None) -> Agent:
    """
    Creates a basic OpenAI agent instance using the specified model.

    Args:
        model (str): The OpenAI model name to use (e.g., 'gpt-4o-2024-08-06', 'o3-mini-2025-01-31').
        instructions (Optional[str]): Custom instructions for the agent.
                                       If None, default instructions are used.

    Returns:
        Agent: An instance of the Agent class.
    """
    default_instructions = """
    You are a helpful assistant that processes text prompts.
    Provide accurate and concise responses based on the prompt provided.
    If the prompt is unclear or ambiguous, state that.
    """
    # Create and return a basic agent
    return Agent(
        name="ParallelProcessorAssistant",
        instructions=instructions or default_instructions,
        model=model, # Use the provided model name
    )

# Function to process a single question file
async def process_question_file(input_file_path: Path, output_dir_path: Path, agent: Agent):
    """
    Reads a question from an input file, gets the agent's response, and writes it to an output file.

    Args:
        input_file_path (Path): Path to the input file containing the question.
        output_dir_path (Path): Path to the directory where the response file should be saved.
        agent (Agent): The agent instance to use for processing.
    """
    output_file_path = output_dir_path / input_file_path.name
    console.print(f"[cyan]Processing:[/cyan] {input_file_path.name} -> {output_file_path.name}")

    try:
        # Read the question (prompt) from the input file
        prompt = input_file_path.read_text(encoding='utf-8')

        if not prompt.strip():
            console.print(f"[yellow]Warning:[/yellow] Skipping empty file: {input_file_path.name}")
            # Optionally create an empty output file or a file indicating skip
            # output_file_path.write_text("Skipped: Input file was empty.", encoding='utf-8')
            return # Skip processing for empty files

        # Run the agent with the prompt
        result = await Runner.run(agent, prompt)
        response = result.final_output

        # Write the response to the output file
        output_file_path.write_text(response, encoding='utf-8')
        console.print(f"[green]Success:[/green]   {input_file_path.name} -> {output_file_path.name}")

    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Input file not found: {input_file_path}")
    except UnicodeDecodeError:
        console.print(f"[bold red]Error:[/bold red] Could not decode file (not UTF-8?): {input_file_path}")
        # Optionally write error info
        # output_file_path.write_text(f"Error: Could not decode file {input_file_path.name}", encoding='utf-8')
    except OpenAIError as e:
        console.print(f"[bold red]Error:[/bold red] OpenAI API error for {input_file_path.name}: {e}")
        # Optionally write error info
        # output_file_path.write_text(f"Error processing prompt in {input_file_path.name}: API Error - {e}", encoding='utf-8')
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to process {input_file_path.name}: {e}")
        # Optionally write error info
        # output_file_path.write_text(f"Error processing prompt in {input_file_path.name}: {e}", encoding='utf-8')


# Function to process all files in a directory in parallel
async def process_directory(input_dir_path: Path, output_dir_path: Path, model_name: str):
    """
    Processes all files in the input directory in parallel using the agent with the specified model.

    Args:
        input_dir_path (Path): Path to the directory containing question files.
        output_dir_path (Path): Path to the directory where response files will be saved.
        model_name (str): The OpenAI model name to use for the agent.
    """
    # Validate input directory
    if not input_dir_path.is_dir():
        console.print(Panel(f"[bold red]Error: Input path '{input_dir_path}' is not a valid directory.[/bold red]"))
        sys.exit(1)

    # Create output directory if it doesn't exist
    try:
        output_dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(Panel(f"[bold red]Error: Could not create output directory '{output_dir_path}': {e}[/bold red]"))
        sys.exit(1)

    # Create the agent instance using the specified model
    agent = create_basic_agent(model=model_name) # Pass the model name

    tasks = []
    console.print(f"Scanning input directory: {input_dir_path}")
    
    file_count = 0
    # Iterate through files in the input directory
    for item in input_dir_path.iterdir():
        # Make sure it's a file and not a directory or other item
        if item.is_file():
            file_count += 1
            # Create a task for each file
            task = asyncio.create_task(
                process_question_file(item, output_dir_path, agent)
            )
            tasks.append(task)
            
    if not tasks:
        console.print(f"[yellow]Warning:[/yellow] No files found in input directory: {input_dir_path}")
        return

    console.print(f"Found {file_count} file(s). Starting parallel processing...")
    
    # Run all tasks concurrently
    # Use return_exceptions=True to prevent gather from stopping on the first error
    # This allows other tasks to complete even if some fail.
    results = await asyncio.gather(*tasks, return_exceptions=True) 
    
    # Check results for exceptions if detailed error reporting is needed at the end
    error_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            error_count += 1
            # Error already printed in process_question_file, but could log more details here if needed
            # task = tasks[i] # Get corresponding task if needed, though less straightforward
            # console.print(f"Task for ??? failed: {result}") # Need a way to link back to filename if needed here

    success_count = len(results) - error_count
    console.print(f"Processing finished. Success: {success_count}, Errors/Skipped: {error_count}")
    console.print(f"[bold green]Responses saved to:[/bold green] {output_dir_path.resolve()}")


# Main execution function
def main():
    """
    Parses command-line arguments and starts the parallel processing of question files.
    """
    parser = argparse.ArgumentParser(
        description="Process question files in parallel using an OpenAI agent."
    )
    parser.add_argument(
        "--input-dir", 
        "-i", 
        type=str, 
        required=True, 
        help="Directory containing the question files."
    )
    parser.add_argument(
        "--output-dir", 
        "-o", 
        type=str, 
        default="output", 
        help="Directory to save the agent's responses (default: ./output)."
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="o3-mini-2025-01-31", # Default to o3-mini-2025-01-31
        help="OpenAI model to use (default: o3-mini-2025-01-31)."
    )
    # Example of adding custom instructions argument:
    # parser.add_argument("--instructions", type=str, default=None, help="Custom instructions file or text for the agent.")

    args = parser.parse_args()

    # Ensure API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        console.print(Panel("[bold red]Error: OPENAI_API_KEY environment variable not set[/bold red]"))
        sys.exit(1)

    input_path = Path(args.input_dir).resolve() # Use resolve for absolute path
    output_path = Path(args.output_dir).resolve() # Use resolve for absolute path
    model_name = args.model # Get the model name from args

    try:
        # Run the main async processing function, passing the model name
        asyncio.run(process_directory(input_path, output_path, model_name))
    except Exception as e:
        # Catch any unexpected errors during async execution setup/teardown
        console.print(Panel(f"[bold red]An unexpected error occurred: {str(e)}[/bold red]"))
        sys.exit(1)

# Entry point for the script
if __name__ == "__main__":
    main()
