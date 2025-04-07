# Parallel Agent Runner

This script (`parallel_agent.py`) processes multiple text files (each containing a prompt) from an input directory in parallel using an OpenAI agent (specifically `gpt-4o-mini`) and saves the responses to an output directory.

## Requirements

-   **uv**: A fast Python package installer and resolver.
-   **OpenAI API Key**: You need an API key from OpenAI.

## Setup

1.  **Install `uv`:**
    `uv` is used to run the script and manage its dependencies directly from the script header. Follow the official installation instructions for your OS:
    -   **macOS / Linux:**
        -   Using Homebrew (macOS):
            ```bash
            brew install uv
            ```
        -   Or using curl:
            ```bash
            curl -LsSf https://astral.sh/uv/install.sh | sh
            ```
    -   **Windows (PowerShell):**
        ```powershell
        irm https://astral.sh/uv/install.ps1 | iex
        ```
    -   **Other methods:** See the [uv documentation](https://docs.astral.sh/uv/).

2.  **Set OpenAI API Key:**
    The script requires the `OPENAI_API_KEY` environment variable to be set. You can set it temporarily in your terminal session:
    ```bash
    export OPENAI_API_KEY='your_api_key_here'
    ```
    Replace `'your_api_key_here'` with your actual key. For a more permanent setup, consider adding this line to your shell's configuration file (e.g., `.zshrc`, `.bashrc`, `.bash_profile`) or using a tool like `direnv`.

## Usage

1.  **Prepare Input Directory:**
    Create a directory (e.g., `prompts`) and place your text files inside it. Each file should contain the text prompt you want the agent to process.
    ```
    prompts/
    ├── question1.txt
    ├── question2.txt
    └── topic_summary.txt
    ```

2.  **Run the Script:**
    Execute the script using `uv run`, providing the input and output directories:
    ```bash
    uv run parallel_agent.py --input-dir prompts --output-dir responses
    ```
    -   `--input-dir` (or `-i`): Specifies the directory containing your prompt files (e.g., `prompts`). This argument is required.
    -   `--output-dir` (or `-o`): Specifies the directory where the agent's responses will be saved (e.g., `responses`). If omitted, it defaults to `./output`.

3.  **Check Output:**
    After the script finishes, the `responses` (or `output`) directory will contain files with the same names as the input files, each holding the corresponding agent response.
    ```
    responses/
    ├── question1.txt  # Contains response to prompts/question1.txt
    ├── question2.txt  # Contains response to prompts/question2.txt
    └── topic_summary.txt # Contains response to prompts/topic_summary.txt
    ```

## How it Works

The script uses `asyncio` to concurrently process each file in the input directory. For each file:
1.  It reads the content as a prompt.
2.  It sends the prompt to the `gpt-4o-mini` model via the `openai-agents` library.
3.  It writes the received response to a corresponding file in the output directory.

Status messages and errors are printed to the console using the `rich` library.