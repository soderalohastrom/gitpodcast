from fastapi import APIRouter, Request, HTTPException, Response
from dotenv import load_dotenv
from app.services.github_service import GitHubService
from app.services.claude_service import ClaudeService
from app.services.openai_service import OpenAIService
from app.core.limiter import limiter
import os
from app.prompts import SYSTEM_FIRST_PROMPT, SYSTEM_SECOND_PROMPT, SYSTEM_THIRD_PROMPT, ADDITIONAL_SYSTEM_INSTRUCTIONS_PROMPT, PODCAST_SSML_PROMPT
from anthropic._exceptions import RateLimitError
from pydantic import BaseModel
from functools import lru_cache
import re
from tempfile import NamedTemporaryFile
import base64

load_dotenv()

router = APIRouter(prefix="/generate", tags=["Claude"])

# Initialize services
github_service = GitHubService()
claude_service = ClaudeService()
openai_service = OpenAIService()

# cache github data for 5 minutes to avoid double API calls from cost and generate
@lru_cache(maxsize=100)
def get_cached_github_data(username: str, repo: str):
    default_branch = github_service.get_default_branch(username, repo)
    if not default_branch:
        default_branch = "main"  # fallback value

    file_tree = github_service.get_github_file_paths_as_list(username, repo)
    readme = github_service.get_github_readme(username, repo)
    file_content = ""
    try:
        file_list = openai_service.get_important_files(file_tree)
        for fpath in file_list:
            content = github_service.get_github_file_content(username, repo, fpath)
            file_content += f"FPATH: fpath CONTENT:{content}"
    except Exception as e:
        print(f"Some error in getting github file content {e}. Proceeding.")

    return {
        "default_branch": default_branch,
        "file_tree": file_tree,
        "readme": readme,
        "file_content": file_content
    }


class ApiRequest(BaseModel):
    username: str
    repo: str
    instructions: str
    api_key: str | None = None
    audio: bool = False  # new param

def calculate_duration(text_line, wpm=135):
    words = len(text_line.split())
    minutes = words / wpm
    seconds = minutes * 60
    return seconds

def ssml_to_webvtt(ssml_content, max_line_length=45, max_words_per_cue=30):
    # Helper function to insert line breaks at appropriate places
    def add_line_breaks(text, max_length):
        words = text.split()
        lines, current_line = [], ""
        for word in words:
            # Check if adding the next word exceeds the length limit
            if len(current_line) + len(word) + 1 > max_length:
                lines.append(current_line)
                current_line = word
            else:
                current_line += (" " if current_line else "") + word
        if current_line:  # Add the remainder of the text if any
            lines.append(current_line)
        return "\n".join(lines)

    # Step 1: Extract text from SSML, remove specific tags, and empty lines
    text_content = re.sub(r'<speak[^>]*>|</speak>|<break[^>]*>', '', ssml_content)
    text_content = re.sub(r'<voice[^>]*>', '\n\n', text_content)
    text_content = re.sub(r'</voice>', '', text_content)
    text_lines = filter(None, [line.strip() for line in text_content.splitlines()])

    # Step 2: Generate WebVTT content with sequential timestamps
    vtt_content = "WEBVTT\n\n"
    cumulative_time = 0.0
    cue_index = 0

    for i, line in enumerate(text_lines):

        # Break the line if it's too long into sub-lines based on word count
        words = line.split()
        sub_lines = []
        for j in range(0, len(words), max_words_per_cue):
            sub_line = ' '.join(words[j:j + max_words_per_cue])
            sub_lines.append(sub_line)

        # Generate VTT for each sub-line
        for sub_line in sub_lines:
            duration = calculate_duration(sub_line)
            start_time = cumulative_time
            end_time = start_time + duration
            cumulative_time = end_time  # Update cumulative time for next line

            # Convert seconds to VTT timestamp format (HH:MM:SS.mmm)
            def seconds_to_timestamp(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                seconds = seconds % 60
                return f"{hours:02}:{minutes:02}:{seconds:06.3f}"

            formatted_sub_line = add_line_breaks(sub_line, max_line_length)
            cue_index += 1
            vtt_content += f"{cue_index}\n"
            vtt_content += f"{seconds_to_timestamp(start_time)} --> {seconds_to_timestamp(end_time)} line:5% align:center\n"
            vtt_content += f"{formatted_sub_line}\n\n"

    return vtt_content


@router.post("")
# @limiter.limit("1/minute;5/day") # TEMP: disable rate limit for growth??
async def generate(request: Request, body: ApiRequest):
    try:
        # Check instructions length
        if len(body.instructions) > 1000:
            return {"error": "Instructions exceed maximum length of 1000 characters"}

        # if body.repo in ["fastapi", "streamlit", "flask", "api-analytics", "monkeytype"]:
        #     return {"error": "Example repos cannot be regenerated"}

        # Get cached github data
        github_data = get_cached_github_data(body.username, body.repo)

        # Get default branch first
        default_branch = github_data["default_branch"]
        file_tree = github_data["file_tree"]
        readme = github_data["readme"]
        file_content = github_data["file_content"]

        # Check combined token count
        combined_content = f"{file_tree}\n{readme}\n{file_content}"
        print(combined_content)
        try:
            token_count = claude_service.count_tokens(combined_content)
            print(f"TOKEN COUNT: {token_count}")
            # Modified token limit check
            if 100000 < token_count < 120000 and not body.api_key:
                return {
                    "error": f"File tree and README combined exceeds token limit (50,000). Current size: {token_count} tokens. This GitHub repository is too large for my wallet, but you can continue by providing your own Anthropic API key.",
                    "token_count": token_count,
                    "requires_api_key": True
                }
            elif token_count > 120000:
                return {
                    "error": f"Repository is too large (>120k tokens) for analysis. OpenAI context is 128k max. Current size: {token_count} tokens."
                }
        except Exception as e:
            print(f"{e} We couldn't get token count, lets proceed with LLM call, nonetheless")
        # Create a temporary file and write the combined_content into it
        with NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as temp_file:
            temp_file.write(combined_content)
            temp_file_path = temp_file.name  # Get the path of the temp file

        try:

            ssml_response = openai_service.call_openai_for_response([temp_file_path], PODCAST_SSML_PROMPT)

            # Process the ssml_response as needed
            # For example, you might want to return or log this response
            print(ssml_response)

        finally:
            # Clean up the temporary file
            os.remove(temp_file_path)

        if not body.audio:
            return {"diagram": "flowchart TB\n    subgraph Input\n        CLI[CLI Interface]:::input\n        API[API Interface]:::input\n    end\n\n    subgraph Orchestration\n        TM[Task Manager]:::core\n        PR[Platform Router]:::core\n    end\n\n    subgraph \"Planning Layer\"\n        TP[Task Planning]:::core\n        subgraph Planners\n            OP[OpenAI Planner]:::planner\n            GP[Gemini Planner]:::planner\n            LP[Local Ollama Planner]:::planner\n        end\n    end\n\n    subgraph \"Finding Layer\"\n        subgraph Finders\n            OF[OpenAI Finder]:::finder\n            GF[Gemini Finder]:::finder\n            LF[Local Ollama Finder]:::finder\n            MF[MLX Finder]:::finder\n        end\n    end\n\n    subgraph \"Execution Layer\"\n        AE[Android Executor]:::executor\n        OE[OSX Executor]:::executor\n    end\n\n    subgraph \"External Services\"\n        direction TB\n        OAPI[OpenAI API]:::external\n        GAPI[Google Gemini API]:::external\n        LAPI[Local Ollama Instance]:::external\n    end\n\n    subgraph \"Platform Tools\"\n        direction TB\n        ADB[Android Debug Bridge]:::platform\n        OSX[OSX System Tools]:::platform\n    end\n\n    subgraph \"Configuration\"\n        direction TB\n        MS[Model Settings]:::config\n        FD[Function Declarations]:::config\n        SP[System Prompts]:::config\n    end\n\n    %% Connections\n    CLI --> TM\n    API --> TM\n    TM --> PR\n    PR --> TP\n    TP --> Planners\n    Planners --> Finders\n    Finders --> AE & OE\n    \n    %% External Service Connections\n    OP & OF -.-> OAPI\n    GP & GF -.-> GAPI\n    LP & LF -.-> LAPI\n    \n    %% Platform Tool Connections\n    AE --> ADB\n    OE --> OSX\n    \n    %% Configuration Connections\n    MS -.-> TM\n    FD -.-> PR\n    SP -.-> TP\n\n    %% Click Events\n    click CLI \"https://github.com/BandarLabs/clickclickclick/blob/main/main.py\"\n    click API \"https://github.com/BandarLabs/clickclickclick/blob/main/api.py\"\n    click MS \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/config/models.yaml\"\n    click FD \"https://github.com/BandarLabs/clickclickclick/tree/main/clickclickclick/config/function_declarations\"\n    click SP \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/config/prompts.yaml\"\n    click OP \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/planner/openai.py\"\n    click GP \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/planner/gemini.py\"\n    click LP \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/planner/local_ollama.py\"\n    click TP \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/planner/task.py\"\n    click OF \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/finder/openai.py\"\n    click GF \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/finder/gemini.py\"\n    click LF \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/finder/local_ollama.py\"\n    click MF \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/finder/mlx.py\"\n    click AE \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/executor/android.py\"\n    click OE \"https://github.com/BandarLabs/clickclickclick/blob/main/clickclickclick/executor/osx.py\"\n\n    %% Styles\n    classDef input fill:#87CEEB,stroke:#333,stroke-width:2px\n    classDef core fill:#4169E1,stroke:#333,stroke-width:2px\n    classDef planner fill:#6495ED,stroke:#333,stroke-width:2px\n    classDef finder fill:#4682B4,stroke:#333,stroke-width:2px\n    classDef executor fill:#1E90FF,stroke:#333,stroke-width:2px\n    classDef external fill:#98FB98,stroke:#333,stroke-width:2px\n    classDef platform fill:#FFA500,stroke:#333,stroke-width:2px\n    classDef config fill:#D3D3D3,stroke:#333,stroke-width:2px",
                    "explanation": 'EXPLANATION'}
        else:
            # ssml_string = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'><voice name='en-US-AvaMultilingualNeural'>Hi The test was successfully completed, now use this place to insert actual data</voice></speak>"
            # Assuming ssml_response is a string with multiple lines
            filtered_ssml_response = '\n'.join(line for line in ssml_response.split('\n') if '```' not in line)

            audio_bytes = claude_service.text_to_mp3(filtered_ssml_response)
            # mp3_bytes = convert_wav_to_mp3(audio_bytes)
            if audio_bytes:
                response = Response(content=audio_bytes, media_type="audio/mpeg", headers={"Content-Disposition": "attachment; filename=explanation.mp3"})
                vtt_content = ssml_to_webvtt(filtered_ssml_response)
                encoded_vtt_content = base64.b64encode(vtt_content.encode('utf-8')).decode('utf-8')
                response.headers["X-VTT-Content"] = encoded_vtt_content
                # Add CORS headers
                response.headers["Access-Control-Expose-Headers"] = "X-VTT-Content"
                response.headers["Access-Control-Allow-Origin"] = "*"
                return response
            else:
                return {"error": "Text to speech is not available. Please set Azure speech credentials in .env"}
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail="Service is currently experiencing high demand. Please try again in a few minutes."
        )
    except Exception as e:
        return {"error": str(e)}


@router.post("/cost")
# @limiter.limit("5/minute") # TEMP: disable rate limit for growth??
async def get_generation_cost(request: Request, body: ApiRequest):
    try:
        # Get file tree and README content
        github_data = get_cached_github_data(body.username, body.repo)
        file_tree = github_data["file_tree"]
        readme = github_data["readme"]

        # Calculate combined token count
        file_tree_tokens = claude_service.count_tokens(file_tree)
        readme_tokens = claude_service.count_tokens(readme)

        # Calculate approximate cost
        # Input cost: $3 per 1M tokens ($0.000003 per token)
        # Output cost: $15 per 1M tokens ($0.000015 per token)
        # Estimate output tokens as roughly equal to input tokens
        input_cost = ((file_tree_tokens * 2 + readme_tokens) + 3000) * 0.000003
        output_cost = 3500 * 0.000015
        estimated_cost = input_cost + output_cost

        # Format as currency string
        cost_string = f"${estimated_cost:.2f} USD"
        return {"cost": cost_string}
    except Exception as e:
        return {"error": str(e)}


def process_click_events(diagram: str, username: str, repo: str, branch: str) -> str:
    """
    Process click events in Mermaid diagram to include full GitHub URLs.
    Detects if path is file or directory and uses appropriate URL format.
    """
    def replace_path(match):
        # Extract the path from the click event
        path = match.group(2).strip('"\'')

        # Determine if path is likely a file (has extension) or directory
        is_file = '.' in path.split('/')[-1]

        # Construct GitHub URL
        base_url = f"https://github.com/{username}/{repo}"
        path_type = "blob" if is_file else "tree"
        full_url = f"{base_url}/{path_type}/{branch}/{path}"

        # Return the full click event with the new URL
        return f'click {match.group(1)} "{full_url}"'

    # Match click events: click ComponentName "path/to/something"
    click_pattern = r'click ([^\s"]+)\s+"([^"]+)"'
    return re.sub(click_pattern, replace_path, diagram)
