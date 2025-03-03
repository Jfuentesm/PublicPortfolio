
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
