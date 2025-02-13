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