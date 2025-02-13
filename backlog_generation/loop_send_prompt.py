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
    mode = config.get("framework", {}).get("mode", "python").lower()

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
                    existing_project_names.add(row[3])  # project name is in the 4th column

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

    # [NEW] Manual prompts CSV (only used in manual mode)
    manual_prompts_filename = f"{time.strftime('%Y%m%d_%H%M%S')}_manualPrompts.csv"
    manual_file_exists = False

    # Loop over each model in the config
    for current_model in MODEL_LIST:

        print(f"\n***** Processing with model: {current_model} *****")

        try:
            for i in range(num_iterations):
                print(f"\n** Iteration {i+1} of {num_iterations} **")

                # Define local API caller function that respects the mode
                def api_caller(prompt):
                    """
                    If mode is 'python', call the OpenRouter API normally.
                    If mode is 'manual', log the prompt to a CSV and return an empty JSON string.
                    """
                    if mode == "python":
                        response_data = send_prompt_to_openrouter(
                            prompt,
                            OPENROUTER_API_KEY,
                            current_model,
                            BASE_URL,
                            log_file=log_filename
                        )
                        return response_data["choices"][0]["message"]["content"]
                    else:
                        # Manual mode: just log the prompt, no real API call
                        nonlocal manual_file_exists
                        with open(manual_prompts_filename, mode='a', newline='', encoding='utf-8') as mfile:
                            writer = csv.writer(mfile)
                            if not manual_file_exists:
                                writer.writerow(["Iteration", "Model", "PromptContent"])
                                manual_file_exists = True
                            writer.writerow([i+1, current_model, prompt])
                        # Return a minimal valid response so parsing won't break
                        return "{}"

                # If we're in manual mode, we only log the main prompt to CSV once per iteration and skip
                if mode == "manual":
                    print("[Manual Mode] Logging the main prompt to CSV. No actual API call or response parsing.")
                    api_caller(PROMPT)
                    # Skip further steps (because we won't receive real data)
                    continue

                # Otherwise, 'python' mode with normal flow
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
                    break  # Move on if an error (e.g. rate-limit) occurs

        except Exception as outer_e:
            # Catch block if something outside iteration breaks for that model
            print(f"Fatal error for model {current_model}: {outer_e}")
            print("Skipping to the next model...\n")

        # Optional pause before moving to next model
        time.sleep(2)

if __name__ == "__main__":
    main()