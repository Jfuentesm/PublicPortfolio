<goal>

Please create a detailed design document for naicsvendorclassification.com
</goal> 

<solution flow> 

- ingest the unique vendors names included in an excel file (local, in /inputs/[COMPANYNAME]_datetime_purchase_transactions.xlsx) 
- normalize and de duplicate (example when capitalization is the only difference or based on other rules)
- create batches of 10 vendor names, that will be passed to an LLM via API as part of a custom prompt (or series of prompts)
- leverage an LLM via API to categorize the vendors included each batch. The taxonomy we will use has 4 levels, we need the solution to do the categorization hierarchically: 
— pass 1: first categorize all the names included in the batches at level 1, 
— pass n (2,3,4): then do a subsequent full pass, presenting the names included new batches of 10 again, this time all the names included in a batch must have the same category assigned at level n-1
- each time the LLM responds via API, the solution will validate that all assigned categories are valid at that level. If not, that batch will be sent again to the LLM.
— use pydantic to validate responses
— hold the taxonomy (4 levels) in a pydantic model
— the prompt will instruct the LLM to respond with a pre-determined JSON structure 
— The prompt (or series of prompts) will instruct the LLM to handle vendor names it doesn’t know in a structured way:
	⁃	 the LLM can use the Tavily tool to do an internet search of the unknown vendor name. This triggers a loop where: 
	⁃	1) a search query is defined, 
	⁃	2) query is sent to Tavily API, 
	⁃	3) Tavily API response is processed, 
	⁃	4) is the Tavily response clarifies, the LLM will assign the category and document the link in the “sources” field. 
	⁃	If the Tavily response is not conclusive or the vendor name is a very common individual person name, then the LLM will assign “classification not possible based on vendor name”
	⁃	the overall output will be an excel file, stored in /outputs/[COMPANYNAME]_datetime_categorizedvendors.xlsx

</solution flow> 

<known technical elements>
	⁃	Use Python packages:
	⁃	Pydantic
	⁃	AzureOpenAI
	⁃	Tavily-Python
	⁃	We need a simple UI where user can upload the inputs, then see the progress of the workflow and download resulting excel file
	⁃	solution will be hosted on AWS eventually, starting with local development using Docker Compose
	⁃	We do not want to have a complex UI: 
	⁃	we will execute the workflow, send the result via email. 
	⁃	We do not need to allow the user to explore the results in our platform, we do not need to have tables they can explore
	⁃	Final result the client can access: final excel to download + a log for archive + general useage statistics for billing (we need to know tokens sent and received from each LLM model as well as number of calls to Tavily API)
	⁃	Confidentiality is a concern:
	⁃	If user uploads fields that are not required, they will be deleted and not taken into account in the workflow
	⁃	If user uploads dangerous data like SSN within the accepted fields, that data should be filtered before the workflow starts as well
</known technical elements>

<output instructions>
Please structure the design document with the following sections:

1. Executive Summary
- Problem statement
- Proposed solution overview
- Key benefits and success metrics

2. System Architecture
- High-level architecture diagram
- Key components and their interactions
- Technology stack recommendations
- Data flow diagrams

3. Detailed Technical Specifications
- Component specifications
- API definitions and interfaces
- Data models and schema
- Security considerations
- Performance requirements

4. Implementation Plan
- Development phases
- Dependencies and prerequisites

5. Risks and Mitigation Strategies
- Technical risks
- Security risks
- Operational risks
- Proposed mitigation approaches

Please provide specific technical details, diagrams, and examples where relevant. The document should be thorough enough for a development team to begin implementation.

</output instructions>

