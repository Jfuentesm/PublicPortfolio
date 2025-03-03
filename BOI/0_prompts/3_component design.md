# prompt creation

<task> help me craft the perfect prompt, using the latest prompt engineering advances such as XML tagging for internal prompt structure and detailed output instructions. I need it to return Detailed Component Diagrams</task>

<pieces of the prompt we want to create>

<goal>
Create Detailed Component Diagrams
   Create separate diagrams showing individual interactions:  
   - **Data Flow Diagram** across the front end, business logic microservices, database layers, and FinCEN integration.  
   - **Deployment Diagram** illustrating how services are grouped (VPC subnets, Docker containers/Lambdas, databases, etc.).
</goal>

<context>
<Opportunity identification>

### 1. **Beneficial Ownership Reporting Compliance Software**  
**Regulatory Requirement:** The Corporate Transparency Act (CTA) and FinCEN’s implementing rules require most U.S. legal entities to report their **beneficial owners** to the Treasury’s FinCEN database. As of Jan 1, 2024, any corporation, LLC, or similar entity (with few exceptions for large or publicly traded firms) must file a report disclosing all individuals who own ≥25% or control the company ([New Laws & Regulations for Small Business Owners in 2025](https://www.bbsi.com/business-owner-resources/new-laws-regulations-small-business-owners-2025#:~:text=Beneficial%20Ownership%20Information%20Reporting)) ([New Laws & Regulations for Small Business Owners in 2025](https://www.bbsi.com/business-owner-resources/new-laws-regulations-small-business-owners-2025#:~:text=This%20requirement%20applies%20to%20most,for%20larger%20publicly%20traded%20companies)). This includes providing each owner’s name, birth date, address, and a government ID number. Companies must also file **updates within 30 days** of any ownership change. Failure to comply carries significant penalties – civil fines up to $500 per day of delay (adjusted to ~$591 with inflation) ([Beneficial Ownership Information | FinCEN.gov](https://www.fincen.gov/boi-faqs#:~:text=the%20BOI%20reporting%20requirements%20may,FAQ%2C%20this%20amount%20is%20%24591)) and potential criminal charges. This regulation creates a **new ongoing compliance burden** for an estimated *tens of millions* of small businesses that never had to report such information before.

**Implementation Timeline:** The rule took effect in 2024. Due to legal challenges, FinCEN extended the initial filing deadline – currently, most existing companies have until **March 21, 2025** to submit their first BOI reports ([BOI Reporting Back in Play With a New Deadline | Paychex](https://www.paychex.com/articles/compliance/beneficial-ownership-information-reporting#:~:text=The%20Treasury%27s%20Financial%20Crimes%20Enforcement,should%20follow%20the%20later%20deadline)) (an extension from the original Jan 2025 deadline). Newly formed companies after Jan 1, 2025 must file within **30 days of formation** ([BOI Reporting Back in Play With a New Deadline | Paychex](https://www.paychex.com/articles/compliance/beneficial-ownership-information-reporting#:~:text=Again%2C%20these%20deadlines%20currently%20are,not%20in%20effect)). Thus, in 2025 virtually all active small companies need to either have filed or be prepared to file on short notice. Going forward, compliance will be continuous: anytime ownership or key control persons change, a new report is due within 30 days. FinCEN is planning to **revise the rule to ease burdens on very small entities** ([BOI Reporting Back in Play With a New Deadline | Paychex](https://www.paychex.com/articles/compliance/beneficial-ownership-information-reporting#:~:text=The%20Treasury%27s%20Financial%20Crimes%20Enforcement,should%20follow%20the%20later%20deadline)), but core requirements are expected to remain. The timeline is urgent – by Q1 2025 tens of millions of reports should be submitted – meaning the window for businesses to adopt solutions is now.

**Market Size & Customer Segments:** Approximately **32 million entities** are expected to be subject to the BOI reporting mandate ([BOI Reporting Back in Play With a New Deadline | Paychex](https://www.paychex.com/articles/compliance/beneficial-ownership-information-reporting#:~:text=Dec,currently%20are%20not%20in%20effect)). The vast majority are small businesses: e.g. local LLCs, single-owner consultancies, family businesses, small nonprofits and shell holding companies. These entities often have **0–10 employees** and minimal administrative staff. Key sub-segments include: 
  - *Small LLCs and S-Corps:* e.g. real estate holding companies, independent contractors’ LLCs, small retailers – typically owner-managed, unaware of CTA requirements.  
  - *Professional Service Firms managing multiple entities:* e.g. accounting or legal firms that help clients form businesses, or companies with many subsidiaries. They may seek software to manage filings for **dozens or hundreds of entities** at once.  
  - *FinTech platforms serving small businesses:* e.g. online incorporation services or registered agent services that could integrate a BOI filing feature to add value for their customers (ZenBusiness, LegalZoom, etc., are already advertising BOI filing assistance ([2025 Regulatory Changes for Small Businesses | ZenBusiness](https://www.zenbusiness.com/blog/new-small-business-regulations/#:~:text=,69))). 

Firmographic data: These businesses are geographically widespread (all states) and span all industries, skewing toward very small firm size. The common factor is lack of compliance expertise – an NFIB survey found many small businesses were unaware of the new law, with **confusion and low early filing rates (only ~400k filed in the first month of availability) ([January 1 Deadline Approaches for Reporting Beneficial Ownership ...](https://www.icsc.com/news-and-views/icsc-exchange/january-1-deadline-approaches-for-reporting-beneficial-ownership-information#:~:text=identifiable%20information%20with%20the%20U,Department%20of%20Treasury%27s))**. This indicates a large addressable market that will scramble to comply as deadlines near.

**Product Features & Tech Specs:** A software solution here would essentially function as a **“BOI compliance manager”** for small entities. Key features: 
  - **Guided Form Filing:** Step-by-step prompts to enter all required owner information, with validation to catch errors (e.g. ensuring ID numbers are in correct format). This would mirror FinCEN’s online form but with a more user-friendly interface and possibly in-app explanations of terms (many users might not know who qualifies as a “beneficial owner”).  
  - **Direct E-Filing Integration:** The product should integrate with FinCEN’s filing system (via an API or at least generate the XML/JSON to upload) so that users can submit reports directly through the app. Successful submission and confirmation from FinCEN should be logged.  
  - **Change Monitoring & Alerts:** Allow the user to store their entity’s ownership info and **flag when updates are needed**. For example, if an owner is removed or added (user updates the record in the app), the software should prompt “You must file an update within 30 days” and, if desired, automatically file the updated BOI report. Calendar reminders for annual review or for the 2025 initial deadline would add value.  
  - **Secure PII Storage:** Because owner data is highly sensitive (PII like passport/driver’s license numbers), strong encryption and security compliance (akin to a tax-filing app) is needed. Role-based access might allow an entrepreneur to share the filing task with their lawyer or CPA securely.  
  - **Multi-Entity Dashboard:** For professionals managing many companies, a dashboard listing all entities and their filing status (Not filed, Filed on X date, Update due, etc.) would be crucial. The product could bulk-import company info from formation documents or Secretary of State registrations to bootstrap the records.  
  - **Compliance Library & Support:** Since rules might change, the software should update in line with FinCEN guidance. Including a help center or AI chatbot to answer “Do I need to report this change?” or “Am I exempt?” based on the latest regulations (exemptions exist for certain larger companies, etc.) could differentiate the product.  
</Opportunity identification>

<High level solution design>
Below is a unified approach, leveraging the **AWS Well-Architected Framework** for secure, scalable, and cost-efficient deployment.

#### 1. Overall Architecture (Text Description)
1. **Client Layer**  
   - **Web Application**: React or Angular front-end hosted on Amazon S3 with Amazon CloudFront for static asset distribution.  
   - **Mobile Application**: Cross-platform (e.g., React Native) to speed up development while retaining near-native performance. Both web and mobile clients communicate via secure APIs over HTTPS.

2. **API & Logic Layer**  
   - **API Gateway**: Amazon API Gateway to expose REST or GraphQL endpoints.  
   - **Microservices**: Business logic implemented as microservices using AWS Lambda for serverless compute or AWS Fargate for container-based workloads—offering flexibility and easy scaling.  
   - **Integration**: Data processing flows to orchestrate beneficial ownership checks, create or update filings, and synchronize with FinCEN’s systems.

3. **Data & Storage Layer**  
   - **Primary Data Store**: Amazon RDS (e.g., PostgreSQL) or Amazon DynamoDB for structured compliance data and high scalability.  
   - **Encryption**: All data at rest encrypted using AWS KMS-managed keys.  
   - **PII Handling**: Confidential personal data stored in a dedicated secured database schema, allowing restricted access and meeting compliance needs.

4. **Security & Compliance**  
   - **Authentication & Authorization**: Amazon Cognito for end-user identity management and SSO capabilities.  
   - **Data Encryption**: TLS/SSL for data in transit; AWS KMS for data encryption at rest.  
   - **Logging & Monitoring**: AWS CloudTrail for API auditing and Amazon CloudWatch for metrics/alerts, ensuring visibility into system health and regulatory audit readiness.

5. **FinCEN Integration**  
   - **Integration Microservice**: Specialized microservice for secure data exchange with FinCEN’s APIs. Maintains queued jobs for filings and updates to handle variable network conditions or FinCEN API latency.  
   - **Error Handling & Retries**: AWS Step Functions or Amazon SQS with dead-letter queues to gracefully handle transient errors and scale batch submission processes.

6. **Deployment & Scalability**  
   - **Infrastructure as Code**: AWS CloudFormation or Terraform for repeatable infrastructure deployments.  
   - **Autoscaling**: Lambda automatically scales in response to demand; for container-based microservices, Amazon ECS/Fargate with auto-scaling policies.  
   - **CI/CD**: AWS CodePipeline and AWS CodeBuild for streamlined build, test, and deployment cycles underneath.  

7. **Mobile Approach**  
   - **Cross-Platform**: React Native shortens time-to-market and simplifies updates by using a single shared codebase. Native device features (camera for document uploads, push notifications, etc.) can still be used for a smooth user experience.
</High level solution design>
</context>



</pieces of the prompt we want to create>


# Final prompt

<goal>
Please create detailed technical component diagrams based on the following specifications
</goal>

<output_format>
Please provide:
1. The diagrams in a clear, readable format
2. A brief explanation of key components
3. Notes on security considerations
4. Any assumptions made while creating the diagrams
</output_format>

<output_requirements>
Generate two separate detailed architectural diagrams:
1. A Data Flow Diagram that shows:
   - All data movement between components
   - Clear indication of front-end components
   - Business logic microservices
   - Database layer interactions
   - FinCEN integration points
   - Security boundaries and encryption points

2. A Deployment Diagram that illustrates:
   - AWS infrastructure components
   - VPC subnet organization
   - Container and Lambda placements
   - Database instance locations
   - Load balancer configurations
   - Security groups and network ACLs
</output_requirements>

<diagram_specifications>
- Use standard UML notation where applicable
- Include clear labels for all components
- Show directional arrows for data flow
- Indicate security zones with different colors/boundaries
- Include legend/key for all symbols used
- Mark all encryption points (data at rest and in transit)
</diagram_specifications>

<system_context>
The system is a Beneficial Ownership Information (BOI) compliance management platform that:
1. Handles sensitive PII data for business owners
2. Integrates with FinCEN's filing system
3. Uses AWS cloud infrastructure
4. Implements microservices architecture
5. Requires high security and compliance standards
6. Supports both web and mobile clients
</system_context>

<technical_requirements>
<High level solution design>
Below is a unified approach, leveraging the **AWS Well-Architected Framework** for secure, scalable, and cost-efficient deployment.

#### 1. Overall Architecture (Text Description)
1. **Client Layer**  
   - **Web Application**: React or Angular front-end hosted on Amazon S3 with Amazon CloudFront for static asset distribution.  
   - **Mobile Application**: Cross-platform (e.g., React Native) to speed up development while retaining near-native performance. Both web and mobile clients communicate via secure APIs over HTTPS.

2. **API & Logic Layer**  
   - **API Gateway**: Amazon API Gateway to expose REST or GraphQL endpoints.  
   - **Microservices**: Business logic implemented as microservices using AWS Lambda for serverless compute or AWS Fargate for container-based workloads—offering flexibility and easy scaling.  
   - **Integration**: Data processing flows to orchestrate beneficial ownership checks, create or update filings, and synchronize with FinCEN’s systems.

3. **Data & Storage Layer**  
   - **Primary Data Store**: Amazon RDS (e.g., PostgreSQL) or Amazon DynamoDB for structured compliance data and high scalability.  
   - **Encryption**: All data at rest encrypted using AWS KMS-managed keys.  
   - **PII Handling**: Confidential personal data stored in a dedicated secured database schema, allowing restricted access and meeting compliance needs.

4. **Security & Compliance**  
   - **Authentication & Authorization**: Amazon Cognito for end-user identity management and SSO capabilities.  
   - **Data Encryption**: TLS/SSL for data in transit; AWS KMS for data encryption at rest.  
   - **Logging & Monitoring**: AWS CloudTrail for API auditing and Amazon CloudWatch for metrics/alerts, ensuring visibility into system health and regulatory audit readiness.

5. **FinCEN Integration**  
   - **Integration Microservice**: Specialized microservice for secure data exchange with FinCEN’s APIs. Maintains queued jobs for filings and updates to handle variable network conditions or FinCEN API latency.  
   - **Error Handling & Retries**: AWS Step Functions or Amazon SQS with dead-letter queues to gracefully handle transient errors and scale batch submission processes.

6. **Deployment & Scalability**  
   - **Infrastructure as Code**: AWS CloudFormation or Terraform for repeatable infrastructure deployments.  
   - **Autoscaling**: Lambda automatically scales in response to demand; for container-based microservices, Amazon ECS/Fargate with auto-scaling policies.  
   - **CI/CD**: AWS CodePipeline and AWS CodeBuild for streamlined build, test, and deployment cycles underneath.  

7. **Mobile Approach**  
   - **Cross-Platform**: React Native shortens time-to-market and simplifies updates by using a single shared codebase. Native device features (camera for document uploads, push notifications, etc.) can still be used for a smooth user experience.
</High level solution design></technical_requirements>

<summarized BOIRAPI userguide>

## BOIR System-to-System API: Condensed Guide

### 1. Introduction
The Beneficial Ownership Information Report (BOIR) collects data on the beneficial owner(s) and company applicant(s) of a reporting company. Users can file BOIR through:
1. Form-based approaches (e.g., PDF, Online forms).
2. **System-to-System** REST API (focus of this guide).

> **Note**: This condensed guide does not describe the underlying BOIR XML schema in detail. That information is located in the separate “BOIR System-to-System XML User Guide.” citeturn0file0

---

### 2. API Access & Credentials
1. **Request Credentials**  
   - Contact FinCEN at [fincen.gov/contact](http://www.fincen.gov/contact) to request system-to-system API credentials.  
   - You will receive a **clientId** and **secret** for each environment (Sandbox vs. Production).

2. **API Environments**  
   - **Sandbox**: `https://boiefiling-api.user-test.fincen.gov/preprod`  
   - **Production**: `https://boiefiling-api.fincen.gov/prod`  

3. **Obtain an Access Token**  
   - Send a `POST` request to `https://iam.fincen.gov/am/oauth2/realms/root/realms/Finance/access_token` with:
     
     **Headers**  
     ```
     Authorization: Basic <base64(clientId:secret)>
     Content-Type: application/x-www-form-urlencoded
     ```
     **Body**  
     ```
     grant_type=client_credentials
     scope=BOSS-EFILE-SANDBOX  (for Sandbox)
     --- or ---
     scope=BOSS-EFILE          (for Production)
     ```

   - **Response** example:  
     ```json
     {
       "access_token": "<access_token>",
       "scope": "BOSS-EFILE",
       "token_type": "Bearer",
       "expires_in": 3599
     }
     ```
   - The `access_token` must be included as a Bearer token in the `Authorization` header of subsequent API requests.

---

### 3. Submission & Tracking Flow
Once you have the **access_token**, your system performs the following steps to file a single BOIR:

1. **Initiate Submission**  
   - `GET /processId`  
   - **Response**:  
     ```json
     {
       "processId": "BOIR230928X6515f3081"
     }
     ```

2. **Upload Attachments** (if reporting any owners/applicants with identifying documents)  
   - `POST /attachments/{processId}/{fileName}`  
   - **Request Body**: The binary data of the attachment (JPG, JPEG, PNG, PDF; size ≤4MB).  
   - **Important**: The `fileName` must match the `OriginalAttachmentFileName` specified in the BOIR XML for each person.

3. **Upload BOIR XML**  
   - `POST /upload/BOIR/{processId}/{xmlFileName}`
   - **Request Body**: The binary data of your BOIR XML file. The server will begin processing your submission.

4. **Track Submission Status**  
   - `GET /submissionStatus/{processId}`
   - **Typical Status Values**  
     - `submission_initiated`
     - `submission_processing`
     - `submission_validation_passed`
     - `submission_validation_failed`
     - `submission_accepted`
     - `submission_rejected`
     - `submission_failed`

5. **Retrieve Transcript**  
   - `GET /transcript/{processId}`
   - **Response**: JSON containing the latest status plus a `pdfBinary` field (Base64-encoded PDF transcript). If the final status is `submission_accepted` or `submission_rejected`, you can decode the PDF for your records.

> **Final Status** can be `submission_accepted`, `submission_rejected`, or `submission_failed`. Anything other than “accepted” or “failed” means FinCEN is still processing or validating the submission.  
> If a submission is “rejected” or “failed,” address the errors and resubmit.

---

### 4. Common Response Codes
The API may return HTTP-level codes alongside a JSON response that clarifies status or error details.

| **Code** | **Meaning**                                    |
|----------|------------------------------------------------|
| 200      | Successful API call                            |
| 400      | Validation Failure (e.g., malformed data)       |
| 401      | Authentication issue (invalid token)           |
| 403      | Authorization issue (forbidden resource)       |
| 404      | Resource not found (bad processId, etc.)       |
| 413      | Payload too large (attachments >4–5MB)         |
| 415      | Unsupported Media Type (invalid file format)   |
| 429      | Throttling (too many requests)                 |
| 5xx      | Internal or Gateway error (try again later)    |

---

### 5. Rejection Error Codes (submission_rejected)
When a BOIR is rejected, you receive an error block under `errors`. Some notable error codes:

| **Code** | **Description**                                                                                                       | **Filing**          | **Party**             | **Resolution**                                                  |
|----------|-----------------------------------------------------------------------------------------------------------------------|---------------------|-----------------------|-----------------------------------------------------------------|
| SBE01    | Could not be processed (transient). Resubmit, contact FinCEN if it persists.                                         | N/A                 | N/A                   | Resubmit as-is.                                                 |
| SBE02    | An **initial** BOIR already exists for this reporting company. Make sure you are not duplicating an initial filing.   | Initial report      | Reporting Company     | If it’s actually an update, correct the filing type.            |
| SBE03    | FinCEN ID for a Company Applicant/Beneficial Owner could not be matched.                                             | Initial report      | Company Applicant / BO| Check that the FinCEN ID(s) are correct.                        |
| SBE04/05 | Update or Correction filing: name/TIN for Reporting Company can’t be matched to a prior BOIR.                         | Update/Correct      | Reporting Company     | Ensure name + TIN match the most recent prior BOIR.             |
| SBE06    | FinCEN ID for a Company Applicant/Beneficial Owner could not be matched.                                             | Update/Correct      | Company Applicant / BO| Validate the FinCEN ID(s).                                      |

If these errors persist, contact the FinCEN Contact Center for assistance.

---

### 6. Key Takeaways
1. **Obtain Credentials & Token**: You cannot proceed without a valid `clientId`, `secret`, and `access_token`.
2. **Follow the Workflow**:
   1. `GET /processId`  
   2. `POST /attachments` for ID documents (if needed)  
   3. `POST /upload/BOIR/{processId}/{xmlFileName}` for the BOIR XML  
   4. `GET /submissionStatus/{processId}` to monitor  
   5. `GET /transcript/{processId}` for the final PDF (Base64-encoded)  
3. **Validation**: Ensure your XML and attachments align precisely with FinCEN’s naming and format standards.  
4. **Error Handling**: Use the returned status codes and error messages to debug or retry your submission.

For complete field definitions, detailed XML requirements, or any legal disclaimers, see FinCEN’s full documentation and the official **BOIR System-to-System XML User Guide**. citeturn0file0
</summarized BOIR API userguide>


<goal>
Please create detailed technical component diagrams based on the following specifications
</goal>