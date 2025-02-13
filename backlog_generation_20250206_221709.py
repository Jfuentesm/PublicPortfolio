'''
Included Files:
- backlog_generation/call_gemini.py
- backlog_generation/config.toml
- backlog_generation/logs
- backlog_generation/loop_send_prompt.py
- backlog_generation/prompt.py
- backlog_generation/prompting_framework.py
- backlog_generation/requirements.txt

'''

# Concatenated Source Code

<file path='backlog_generation/call_gemini.py'>
import requests
import json

def main():
    # URL with your specific endpoint and API key
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyBE-gyfXGOpUMPXcfxdIOOU4oWZWr1oTf0"
    
    # The data payload mirrors your cURL command
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Explain how AI works"}
                ]
            }
        ]
    }
    
    # Required headers (Content-Type is important for JSON data)
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make a POST request to the Gemini API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Print the full JSON response for clarity
        data = response.json()
        print(json.dumps(data, indent=2))
    
    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., network errors or 400/500 responses)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
</file>

<file path='backlog_generation/config.toml'>
[openrouter]
api_key = "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"
models = [
  #"google/gemini-2.0-pro-exp-02-05:free",
  # "google/gemini-2.0-flash-lite-preview-02-05:free",
  #"google/gemini-2.0-flash-thinking-exp:free",
  #"google/gemini-exp-1206:free",
  #"google/gemini-2.0-flash-thinking-exp-1219:free",
  #"google/gemini-2.0-flash-exp:free",
  "qwen/qwen2.5-vl-72b-instruct:free",
  #"deepseek/deepseek-r1-distill-llama-70b:free",
  #"deepseek/deepseek-r1:free",
  #"sophosympatheia/rogue-rose-103b-v0.2:free"
]
base_url = "https://openrouter.ai/api/v1"

[framework]
max_iterations = 1
validation_threshold = 0.7
refinement_rounds = 2
</file>

<file path='backlog_generation/logs'>
Error reading /Users/juanfuentes/localcoding/PublicPortfolio/backlog_generation/logs: [Errno 21] Is a directory: '/Users/juanfuentes/localcoding/PublicPortfolio/backlog_generation/logs'
</file>

<file path='backlog_generation/loop_send_prompt.py'>
import toml
import requests
import time
import csv
import os
import json
from prompt import prompt_content
from prompting_framework import PromptingFramework

def send_prompt_to_openrouter(prompt, openrouter_api_key, model, base_url, log_file=None):
    """
    Sends a prompt to the specified model via the OpenRouter API, returning the JSON response.
    Automatically logs request and response data if log_file is provided.
    If the response contains an 'error' key (even if status_code == 200), raises an exception.
    """
    url = f"{base_url}/chat/completions"

    # Sanitize the API key in the log by masking it in the Authorization header
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}",
        "X-Title": "Custom Chat",
        "Accept": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": prompt
            }
        ],
        "max_tokens": 4000
    }

    try:
        response = requests.post(url, headers=headers, json=data)
    except Exception as ex:
        # Log the exception if an error occurs during the request
        if log_file is not None:
            with open(log_file, 'a', encoding='utf-8') as lf:
                lf.write("===== API CALL EXCEPTION =====\n")
                lf.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                lf.write(f"Request URL: {url}\n")
                masked_headers = dict(headers)
                masked_headers["Authorization"] = "Bearer ***REDACTED***"
                lf.write(f"Headers (sanitized): {json.dumps(masked_headers, indent=2)}\n")
                lf.write(f"Request Data: {json.dumps(data, indent=2)}\n")
                lf.write(f"Exception: {str(ex)}\n")
                lf.write("===== END OF CALL =====\n\n")
        raise

    # Log request/response details
    if log_file is not None:
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write("===== API CALL START =====\n")
            lf.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            lf.write(f"Request URL: {url}\n")
            masked_headers = dict(headers)
            masked_headers["Authorization"] = "Bearer ***REDACTED***"
            lf.write(f"Headers (sanitized): {json.dumps(masked_headers, indent=2)}\n")
            lf.write(f"Request Data: {json.dumps(data, indent=2)}\n")
            lf.write(f"Status Code: {response.status_code}\n")
            lf.write(f"Response Text: {response.text}\n")
            lf.write("===== API CALL END =====\n\n")

    if response.status_code == 200:
        response_data = response.json()
        # Check if the provider returned an error inside the JSON, e.g. rate-limit
        if "error" in response_data:
            error_dict = response_data["error"]
            error_msg = error_dict.get("message", "An unknown error occurred.")
            error_code = error_dict.get("code", "n/a")
            raise Exception(f"OpenRouter returned error: {error_msg} (Code: {error_code})")
        return response_data
    else:
        # Log non-200 responses
        error_message = f"Request failed with status code {response.status_code}: {response.text}"
        if log_file is not None:
            with open(log_file, 'a', encoding='utf-8') as lf:
                lf.write("===== API CALL ERROR =====\n")
                lf.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                lf.write(error_message + "\n")
                lf.write("===== END OF CALL =====\n\n")
        raise Exception(error_message)

def main():
    # 1) Load configuration from config.toml
    config_path = "config.toml"
    config = toml.load(config_path)
    OPENROUTER_API_KEY = config["openrouter"]["api_key"]
    MODEL_LIST = config["openrouter"]["models"]
    BASE_URL = config["openrouter"]["base_url"]

    # Framework parameters
    num_iterations = config.get("framework", {}).get("max_iterations", 2)

    # Create the logs folder (if not exist) and define a timestamped log filename
    os.makedirs('logs', exist_ok=True)
    log_filename = os.path.join('logs', f"run_log_{time.strftime('%Y%m%d_%H%M%S')}.log")

    # Initialize the prompting framework
    framework = PromptingFramework()
    
    # 2) Set your base prompt
    PROMPT_BASE = prompt_content

    # 3) CSV setup
    csv_filename = "responses.csv"
    file_exists = os.path.isfile(csv_filename)

    # Read existing project names for exclusion
    existing_project_names = set()
    if file_exists:
        with open(csv_filename, mode='r', encoding='utf-8') as existing_csv:
            reader = csv.reader(existing_csv)
            # skip header
            next(reader, None)
            for row in reader:
                if len(row) > 3:
                    existing_project_names.add(row[3])  # project name is in 4th col if we add model in 3rd

    # Create exclusion prompt
    exclusion_text = "\n".join(sorted(existing_project_names)) if existing_project_names else ""
    exclusion_prompt = (
        "\n<already_used_projects>\n"
        f"The following project names have already been used. Please DO NOT repeat them "
        f"or produce highly similar ideas:\n{exclusion_text}\n"
        "</already_used_projects>\n"
        "\nConstraint: Generate new ideas that do not overlap with these existing names.\n"
    )

    # Final combined prompt
    PROMPT = PROMPT_BASE + exclusion_prompt

    # Loop over each model in the config
    for current_model in MODEL_LIST:

        print(f"\n***** Processing with model: {current_model} *****")

        try:
            for i in range(num_iterations):
                print(f"\n** Iteration {i+1} of {num_iterations} **")

                # Define local API caller that logs this iteration as well
                def api_caller(prompt):
                    response_data = send_prompt_to_openrouter(
                        prompt,
                        OPENROUTER_API_KEY,
                        current_model,
                        BASE_URL,
                        log_file=log_filename
                    )
                    return response_data["choices"][0]["message"]["content"]

                try:
                    # Initial ideation
                    response_json = send_prompt_to_openrouter(
                        PROMPT,
                        OPENROUTER_API_KEY,
                        current_model,
                        BASE_URL,
                        log_file=log_filename
                    )

                    initial_ideas = json.loads(response_json["choices"][0]["message"]["content"])
                
                    # Process each idea through the framework stages
                    refined_ideas = []
                    for idea in initial_ideas:
                        print(f"\nProcessing idea: {idea['project_name']}")
                        refined_idea = framework.process_idea(idea, api_caller)
                        refined_ideas.append(refined_idea)

                    # Write results to CSV
                    with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
                        writer = csv.writer(csv_file)
                        if not file_exists:
                            writer.writerow([
                                "Iteration",
                                "Timestamp",
                                "Model",
                                "Project Name",
                                "Business Problem",
                                "Core Components",
                                "Key Technologies",
                                "Architecture Overview",
                                "Unique Selling Points",
                                "Implementation Complexity",
                                "Estimated Timeline",
                                "Portfolio Value",
                                "Potential Extensions",
                                "Validation Score",
                                "Risk Assessment",
                                "Implementation Details"
                            ])
                            file_exists = True

                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                        for idea in refined_ideas:
                            tech_sol = idea.get("technical_solution", {})
                            validation = idea.get("validation", {})

                            writer.writerow([
                                i+1,
                                timestamp,
                                current_model,
                                idea.get("project_name", ""),
                                idea.get("business_problem", ""),
                                "; ".join(tech_sol.get("core_components", [])),
                                "; ".join(tech_sol.get("key_technologies", [])),
                                tech_sol.get("architecture_overview", ""),
                                "; ".join(tech_sol.get("unique_selling_points", [])),
                                idea.get("implementation_complexity", ""),
                                idea.get("estimated_timeline", ""),
                                idea.get("portfolio_value", ""),
                                "; ".join(idea.get("potential_extensions", [])),
                                validation.get("score", ""),
                                validation.get("risk_assessment", ""),
                                idea.get("implementation_details", "")
                            ])

                    print(f"Refined ideas successfully appended to {csv_filename}.")

                except Exception as e:
                    print(f"Error during iteration {i+1} with model {current_model}: {e}")
                    print(f"Skipping remaining iterations for model {current_model}...\n")
                    break  # Move to the next model if there's an error (rate-limit or otherwise)

        except Exception as outer_e:
            # This catch block helps if something outside iteration breaks for that model
            print(f"Fatal error for model {current_model}: {outer_e}")
            print("Skipping to the next model...\n")

        # Optional pause before moving to next model
        time.sleep(2)

if __name__ == "__main__":
    main()
</file>

<file path='backlog_generation/prompt.py'>
# prompt.py

prompt_content = """
<system_instruction>
You are tasked with generating innovative sustainability automation project ideas that would be valuable additions to a technology portfolio. These ideas should be technically feasible, demonstrate advanced capabilities, and address real business needs in corporate sustainability.

Consider the following technical capabilities:
- Python-based development
- LLM integration
- Knowledge graph implementation
- RAG systems
- UI development with Streamlit
- Ontology management

Focus areas should include but not be limited to:
- Regulatory compliance automation
- Sustainability risk assessment
- ESG data analysis and reporting
- Value chain optimization
- Impact measurement and management
</system_instruction>

<few_shot_examples>
{
    "example_1": {
        "project_name": "CSRD Value Chain Automation Engine",
        "business_problem": "Consulting teams need to efficiently analyze and map complex corporate value chains for CSRD compliance, a process that is typically manual and time-consuming.",
        "technical_solution": {
            "core_components": [
                "Natural Language Processing Pipeline",
                "Value Chain Graph Database",
                "Automated Report Generator"
            ],
            "key_technologies": [
                "LangChain",
                "Python",
                "Neo4j/NetworkX",
                "Large Language Models"
            ],
            "architecture_overview": "RAG-based system that processes company documentation to automatically extract and visualize value chain relationships, with AI-powered relationship inference",
            "unique_selling_points": [
                "Automated value chain mapping",
                "Relationship inference engine",
                "Visual network analysis",
                "Report generation capabilities"
            ]
        },
        "implementation_complexity": "Advanced",
        "estimated_timeline": "8 weeks",
        "portfolio_value": "Demonstrates expertise in both technical implementation and regulatory domain knowledge",
        "potential_extensions": [
            "Industry comparison module",
            "Risk propagation analysis",
            "Supplier sustainability scoring"
        ]
    },
    "example_2": {
        "project_name": "IRO Assessment AI Platform",
        "business_problem": "Organizations struggle to systematically identify, assess, and prioritize Impact, Risks, and Opportunities (IROs) for sustainability reporting.",
        "technical_solution": {
            "core_components": [
                "IRO Generation Engine",
                "Materiality Assessment Module",
                "Financial Impact Calculator"
            ],
            "key_technologies": [
                "LangChain",
                "Streamlit",
                "LLMs",
                "Python Analytics Libraries"
            ],
            "architecture_overview": "Web-based platform combining LLM-powered analysis with structured assessment frameworks",
            "unique_selling_points": [
                "Automated IRO generation",
                "Dual materiality assessment",
                "Financial impact quantification",
                "Stakeholder-specific reporting"
            ]
        },
        "implementation_complexity": "Intermediate",
        "estimated_timeline": "6 weeks",
        "portfolio_value": "Shows ability to combine AI with structured business frameworks",
        "potential_extensions": [
            "Scenario analysis module",
            "Stakeholder engagement tracker",
            "Automated action plan generator"
        ]
    },
    "example_3": {
        "project_name": "CSRD Knowledge Graph Analytics",
        "business_problem": "Need to analyze and derive insights from Wave 1 CSRD reports to identify patterns, best practices, and benchmark against peers.",
        "technical_solution": {
            "core_components": [
                "Document Processing Pipeline",
                "Knowledge Graph Builder",
                "Query Interface"
            ],
            "key_technologies": [
                "owlready2",
                "RDFlib",
                "SpaCy",
                "LLMs for text extraction"
            ],
            "architecture_overview": "Knowledge graph-based system that processes CSRD reports and creates queryable semantic relationships",
            "unique_selling_points": [
                "Semantic relationship mapping",
                "Cross-company analysis",
                "Pattern identification",
                "Benchmark generation"
            ]
        },
        "implementation_complexity": "Advanced",
        "estimated_timeline": "10 weeks",
        "portfolio_value": "Demonstrates advanced knowledge graph implementation and domain expertise",
        "potential_extensions": [
            "Visual graph explorer",
            "Automated reporting insights",
            "Industry taxonomy builder"
        ]
    }
}
</few_shot_examples>


<input_parameters>
{
    "number_of_ideas": ${NUMBER_OF_IDEAS_REQUESTED},
    "complexity_level": ${COMPLEXITY_LEVEL}, // "beginner" | "intermediate" | "advanced"
    "time_frame": ${ESTIMATED_DEVELOPMENT_TIME} // in weeks
}
</input_parameters>

<output_format>
Return a JSON array of ideas. Each idea must have the following structure (no extra keys):
[
  {
    "project_name": "",
    "business_problem": "",
    "technical_solution": {
      "core_components": [],
      "key_technologies": [],
      "architecture_overview": "",
      "unique_selling_points": []
    },
    "implementation_complexity": "",
    "estimated_timeline": "",
    "portfolio_value": "",
    "potential_extensions": []
  },
  ...
]
</output_format>

<constraints>
- Projects must be distinct from existing implementations
- Solutions should be scalable and maintainable
- Ideas should demonstrate innovative use of AI/ML technologies
- Projects should address real-world sustainability challenges
- Implementation should be feasible for a single developer
</constraints>

<evaluation_criteria>
- Technical sophistication
- Business value
- Innovation level
- Portfolio impact
- Implementation feasibility
</evaluation_criteria>

Please respond strictly with a **valid JSON array** of idea objects, with no additional text outside the JSON. Do NOT wrap the JSON.
"""
</file>

<file path='backlog_generation/prompting_framework.py'>
# prompting_framework.py
from typing import Dict, List
import json

class PromptingStage:
    def __init__(self, name: str, prompt_template: str):
        self.name = name
        self.prompt_template = prompt_template

class PromptingFramework:
    def __init__(self):
        self.stages = [
            PromptingStage("ideation", """
                {base_prompt}
                Additional Context: Focus on generating initial project concepts.
                Previous Ideas: {previous_ideas}
            """),
            PromptingStage("validation", """
                Review and validate the following project idea:
                {project_idea}
                
                Evaluate:
                1. Technical feasibility
                2. Business value alignment
                3. Implementation risks
                4. Resource requirements
                
                Return a JSON object with your assessment and suggested improvements.
            """),
            PromptingStage("refinement", """
                Based on the validation feedback, enhance the following project idea:
                {project_idea}
                {validation_feedback}
                
                Provide a refined version with:
                1. More detailed technical specifications
                2. Implementation steps
                3. Risk mitigation strategies
                4. Success metrics
                
                Return the enhanced project as a JSON object.
            """)
        ]
        self.results = {}

    def process_idea(self, idea: Dict, api_caller) -> Dict:
        """Process a single idea through all stages"""
        current_idea = idea
        
        for stage in self.stages[1:]:  # Skip ideation stage for existing ideas
            response = api_caller(
                stage.prompt_template.format(
                    project_idea=json.dumps(current_idea, indent=2),
                    validation_feedback=self.results.get(f"{idea['project_name']}_validation", "")
                )
            )
            self.results[f"{idea['project_name']}_{stage.name}"] = response
            current_idea = self.merge_feedback(current_idea, response)
            
        return current_idea

    @staticmethod
    def merge_feedback(original: Dict, feedback: Dict) -> Dict:
        """Merge feedback into the original idea"""
        # Implementation depends on the specific feedback structure
        # This is a simplified version
        original.update(feedback)
        return original
</file>

<file path='backlog_generation/requirements.txt'>
requests
toml
</file>

"""
<goal>


</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>
"""
