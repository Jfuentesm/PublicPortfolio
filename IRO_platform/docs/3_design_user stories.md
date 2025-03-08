# ESG/Sustainability Analyst

### User Story 1: Materiality Assessment Dashboard Access
**As an ESG/Sustainability Analyst, I need to access a comprehensive dashboard showing IRO distributions by stage, type, and materiality scores**

**Key questions:** 
- What's the current status of all IROs across the organization?
- Which IROs have the highest materiality scores?
- How are IROs distributed across different types (Risks, Opportunities, Impacts)?
- How many IROs are in each stage of the review process?

**Info views that might answer these questions:**

1. **Info View: IRO Distribution by Type**
   - **Description:** Visualizes the distribution of IROs by type (Risk, Opportunity, Impact)
   - **Datapoints needed and table of origin:**
     - IRO counts by type (from `iro` table, grouping by `type`)
     - Type categories (from `iro.type` field)
     - Optional filter by tenant (from `iro.tenant_id` joining with `tenant_config`)

2. **Info View: Materiality Matrix**
   - **Description:** Scatter plot showing IROs positioned by impact materiality and financial materiality
   - **Datapoints needed and table of origin:**
     - IRO IDs and titles (from `iro` joined with `iro_version` via `current_version_id`)
     - Impact materiality scores (from `impact_assessment.impact_materiality_score` where `iro_id` matches)
     - Financial materiality scores (from `risk_opp_assessment.financial_materiality_score` where `iro_id` matches)
     - IRO types (from `iro.type`)

3. **Info View: High Priority IROs Table**
   - **Description:** Sortable table showing highest-scoring IROs with key details
   - **Datapoints needed and table of origin:**
     - IRO ID and title (from `iro` joined with `iro_version` via `current_version_id`)
     - IRO type (from `iro.type`)
     - Current stage (from `iro.current_stage`)
     - Impact score (from `impact_assessment.impact_materiality_score`)
     - Financial score (from `risk_opp_assessment.financial_materiality_score`) 
     - Last assessment date (from `iro.last_assessment_date`)

### User Story 2: Impact Assessment Creation and Editing
**As an ESG/Sustainability Analyst, I need to create and edit detailed impact materiality assessments for IROs classified as "Impact"**

**Key questions:** 
- How do I thoroughly assess the materiality of an impact?
- What criteria should be used for scale, scope, and irremediability?
- How are likelihood factors incorporated into the assessment?
- How do all these factors combine into an overall impact materiality score?

**Info views that might answer these questions:**

1. **Info View: Impact Assessment Form**
   - **Description:** Form allowing analysts to assess the materiality of impact IROs
   - **Datapoints needed and table of origin:**
     - IRO details (from `iro` joined with `iro_version` where `type = 'Impact'`)
     - Scale score with rationale (stored in `impact_assessment.scale_score` and `scale_rationale`)
     - Scope score with rationale (stored in `impact_assessment.scope_score` and `scope_rationale`)
     - Irremediability score with rationale (stored in `impact_assessment.irremediability_score` and `irremediability_rationale`)
     - Likelihood score with rationale (stored in `impact_assessment.likelihood_score` and `likelihood_rationale`)
     - Actual or potential impact classification (stored in `impact_assessment.actual_or_potential`)
     - Human rights relevance (stored in `impact_assessment.related_to_human_rights`)
     - Time horizon selection (stored in `impact_assessment.time_horizon`)
     - Overall rationale (stored in `impact_assessment.overall_rationale`)

2. **Info View: Impact Scoring Definitions**
   - **Description:** Reference guide for scoring criteria in impact assessments
   - **Datapoints needed and table of origin:**
     - Dimension definitions (from `impact_materiality_def.dimension`)
     - Score definitions by value (from `impact_materiality_def.definition_text` where `score_value` = selected value)
     - Current scoring version (from `impact_materiality_def.version_num` where `valid_to` is null)

### User Story 3: Financial Materiality Assessment
**As an ESG/Sustainability Analyst, I need to create and edit financial materiality assessments for IROs classified as "Risk" or "Opportunity"**

**Key questions:** 
- How do I appropriately assess financial materiality for risks and opportunities?
- What financial impact dimensions should I consider? 
- How does the risk/opportunity likelihood factor into the overall score?
- How can I provide consistent rationales across multiple assessments?

**Info views that might answer these questions:**

1. **Info View: Financial Materiality Assessment Form**
   - **Description:** Form allowing analysts to assess the financial materiality of risks and opportunities
   - **Datapoints needed and table of origin:**
     - IRO details (from `iro` joined with `iro_version` where `type` in ('Risk', 'Opportunity'))
     - Workforce risk score and rationale (stored in `risk_opp_assessment.workforce_risk` and `workforce_risk_rationale`)
     - Operational risk score and rationale (stored in `risk_opp_assessment.operational_risk` and `operational_risk_rationale`) 
     - Cost of capital risk score and rationale (stored in `risk_opp_assessment.cost_of_capital_risk` and `cost_of_capital_risk_rationale`)
     - Reputational risk score and rationale (stored in `risk_opp_assessment.reputational_risk` and `reputational_risk_rationale`)
     - Legal/compliance risk score and rationale (stored in `risk_opp_assessment.legal_compliance_risk` and `legal_compliance_risk_rationale`)
     - Likelihood score and rationale (stored in `risk_opp_assessment.likelihood_score` and `likelihood_rationale`)
     - Time horizon selection (stored in `risk_opp_assessment.time_horizon`)
     - Overall rationale (stored in `risk_opp_assessment.overall_rationale`)

2. **Info View: Financial Materiality Weighted Calculation**
   - **Description:** Automated calculation showing how individual risk dimensions combine to form overall financial materiality score
   - **Datapoints needed and table of origin:**
     - Dimension weights (from `fin_materiality_weights` table where `valid_to` is null)
     - Individual dimension scores (from the various risk score fields in `risk_opp_assessment`)
     - Financial magnitude definitions (from `fin_materiality_magnitude_def` where `valid_to` is null)
     - Calculated financial magnitude (stored in `risk_opp_assessment.financial_magnitude_score`)
     - Final financial materiality score (stored in `risk_opp_assessment.financial_materiality_score`)

### User Story 4: IRO Creation and Classification
**As an ESG/Sustainability Analyst, I need to create and classify new IROs (Impacts, Risks, Opportunities)**

**Key questions:** 
- How do I properly classify a new IRO as Impact, Risk, or Opportunity?
- What information is required to document an IRO completely?
- How do I connect IROs to relevant sustainability topics and ESRS standards?
- How can I track different versions of an IRO as it evolves?

**Info views that might answer these questions:**

1. **Info View: IRO Creation Form**
   - **Description:** Form allowing creation of new IRO records with proper classification
   - **Datapoints needed and table of origin:**
     - IRO type selector (stored in `iro.type`)
     - IRO title (stored in `iro_version.title`)
     - IRO description (stored in `iro_version.description`) 
     - ESRS standard reference (stored in `iro.esrs_standard`)
     - Source of IRO (stored in `iro.source_of_iro`)
     - Sustainability topic hierarchy (stored in `iro_version.sust_topic_level1`, `sust_topic_level2`, `sust_topic_level3`)
     - Value chain position (stored in `iro_version.value_chain_lv1`, `value_chain_lv2`)
     - Economic activity information (stored in `iro_version.economic_activity`)
     - Current stage dropdown (stored in `iro.current_stage`)

2. **Info View: IRO Version History**
   - **Description:** Timeline view of changes to an IRO through multiple versions
   - **Datapoints needed and table of origin:**
     - Version numbers and dates (from `iro_version.version_number` and `created_on`)
     - Changes between versions (comparing fields across versions)
     - Version creators (from `iro_version.created_by` joined with user information)
     - Parent version references (from `iro_version.parent_version_id`)

### User Story 5: IRO Relationship Mapping
**As an ESG/Sustainability Analyst, I need to establish and visualize relationships between different IROs**

**Key questions:** 
- How do different IROs relate to each other?
- Which IROs cause or influence other IROs?
- Are there clusters of related IROs that should be assessed together?
- How can I track IRO dependencies across the value chain?

**Info views that might answer these questions:**

1. **Info View: IRO Relationship Manager**
   - **Description:** Interface for creating and managing relationships between IROs
   - **Datapoints needed and table of origin:**
     - Source and target IROs (stored in `iro_relationship.source_iro_id` and `target_iro_id`)
     - Relationship type (stored in `iro_relationship.relationship_type`)
     - Relationship notes (stored in `iro_relationship.notes`)
     - Creation metadata (stored in `iro_relationship.created_by` and `created_on`)

2. **Info View: IRO Relationship Graph**
   - **Description:** Visual network graph showing relationships between IROs
   - **Datapoints needed and table of origin:**
     - IRO nodes (from `iro` joined with `iro_version` for current titles)
     - Relationship edges (from `iro_relationship` for connections)
     - IRO types for color coding (from `iro.type`)
     - Relationship types for edge styling (from `iro_relationship.relationship_type`)

### User Story 6: Review and Approval Workflow Participation
**As an ESG/Sustainability Analyst, I need to participate in the IRO review and approval workflow process**

**Key questions:** 
- Which IROs require my review or input?
- How do I submit an IRO for review by others?
- What stage is each IRO at in the approval process?
- How do I track reviewer feedback and incorporate changes?

**Info views that might answer these questions:**

1. **Info View: My Review Tasks**
   - **Description:** Dashboard showing IROs assigned to the analyst for review
   - **Datapoints needed and table of origin:**
     - Pending reviews (from `review` table where `reviewer_id` matches current user and `status = 'In_Review'`)
     - IRO details for reviews (joining `review` with `iro` and `iro_version`)
     - Review due dates (if tracked in system)
     - Time since assignment (calculating from `review.created_on`)

2. **Info View: IRO Stage Management**
   - **Description:** Interface for moving IROs through approval workflow stages
   - **Datapoints needed and table of origin:**
     - Current stage (from `iro.current_stage`)
     - Stage transition options (based on workflow rules)
     - Required approvers (system configuration)
     - Review notes (from `review.notes`)
     - Signoff information (from `signoff` table)
     - Audit trail of stage changes (from `audit_trail` where `entity_type = 'IRO'` and action involves stage changes)

### User Story 7: Historical Assessment Analysis
**As an ESG/Sustainability Analyst, I need to analyze how IRO assessments have changed over time**

**Key questions:** 
- How have our materiality assessments evolved over multiple assessment cycles?
- Which IROs have seen significant score changes?
- What trends exist in our impact and financial materiality assessments?
- How do previous assessments compare to current ones?

**Info views that might answer these questions:**

1. **Info View: IRO Assessment History**
   - **Description:** Timeline showing changes in materiality assessments for a specific IRO
   - **Datapoints needed and table of origin:**
     - IRO details (from `iro` and `iro_version`)
     - Historical impact assessments (from `impact_assessment` ordered by `created_on`)
     - Historical risk/opportunity assessments (from `risk_opp_assessment` ordered by `created_on`) 
     - Assessment score trends (calculated from historical scores)
     - Assessment count (from `iro.assessment_count`)

2. **Info View: Assessment Comparison Tool**
   - **Description:** Side-by-side comparison of assessments from different time periods
   - **Datapoints needed and table of origin:**
     - Assessment pairs for comparison (from `impact_assessment` or `risk_opp_assessment` by date ranges)
     - Score differences (calculated from selected assessments)
     - Rationale changes (comparing rationale fields between assessments)
     - Count of changed scores (calculated from comparison)

### User Story 8: ESRS Standards Compliance Tracking
**As an ESG/Sustainability Analyst, I need to track IRO coverage against ESRS standards and identify compliance gaps**

**Key questions:** 
- Which ESRS standards are covered by our current IROs?
- Are there mandatory standards that don't have associated IROs?
- How complete is our coverage of material topics required by ESRS?
- What IROs need to be created to ensure complete ESRS compliance?

**Info views that might answer these questions:**

1. **Info View: ESRS Coverage Map**
   - **Description:** Visualization of IRO coverage across all relevant ESRS standards
   - **Datapoints needed and table of origin:**
     - ESRS standards (from `iro.esrs_standard`, plus reference list of all standards)
     - IRO counts by standard (grouping IROs by `esrs_standard`)
     - Gap analysis (comparing existing coverage to required standards)
     - IRO types by standard (analyzing distribution of Impact, Risk, and Opportunity by standard)

2. **Info View: ESRS Standard Detail**
   - **Description:** Detailed view of IROs related to a specific ESRS standard
   - **Datapoints needed and table of origin:**
     - Selected ESRS standard (filter criterion)
     - IROs related to standard (from `iro` where `esrs_standard` matches selection)
     - Materiality scores for these IROs (from relevant assessment tables)
     - Current stages (from `iro.current_stage`)
     - Documentation completeness metrics (calculated from required fields)

### User Story 9: Data Import and Bulk Update Capabilities 
**As an ESG/Sustainability Analyst, I need to import and bulk update IRO data from external sources**

**Key questions:** 
- How can I efficiently import multiple IROs from other systems?
- How can I update numerous IROs with data from external assessments?
- How do I validate imported data before committing changes?
- How do I track the source of imported data?

**Info views that might answer these questions:**

1. **Info View: Data Import Interface**
   - **Description:** Tool for uploading and mapping external data to system IRO fields
   - **Datapoints needed and table of origin:**
     - Import template structure (system-defined)
     - Mapping controls (associating external data fields with system fields)
     - Validation rules (system-defined constraints for each field)
     - Target tables and fields (based on data type being imported)
     - Source tracking (stored in `iro.source_of_iro` or audit trail)

2. **Info View: Bulk Update Preview**
   - **Description:** Validation interface showing changes before they're applied
   - **Datapoints needed and table of origin:**
     - Current values (from relevant tables based on update type)
     - Proposed changes (from import data)
     - Validation issues (calculated from business rules)
     - Affected record count (calculated from import scope)
     - Change summary statistics (aggregated from proposed changes)

### User Story 10: Sustainability Topic Analysis
**As an ESG/Sustainability Analyst, I need to analyze IROs by sustainability topic to identify coverage patterns and gaps**

**Key questions:** 
- How are our IROs distributed across sustainability topics?
- Which topics have the highest materiality scores?
- Are there sustainability topics with insufficient coverage?
- How do specific topics compare in terms of impact versus financial materiality?

**Info views that might answer these questions:**

1. **Info View: Topic Heatmap**
   - **Description:** Matrix visualization showing materiality scores across sustainability topics
   - **Datapoints needed and table of origin:**
     - Sustainability topics (from `iro_version.sust_topic_level1` and `sust_topic_level2`)
     - IRO counts by topic (grouping by topics)
     - Average impact scores by topic (aggregating from `impact_assessment`)
     - Average financial scores by topic (aggregating from `risk_opp_assessment`)
     - Combined materiality by topic (calculated from both score types)

2. **Info View: Topic Detail Drill-down**
   - **Description:** Detailed analysis of a selected sustainability topic and its related IROs
   - **Datapoints needed and table of origin:**
     - Selected topic (filter criterion)
     - IROs in topic (from `iro_version` where topic fields match selection)
     - IRO types distribution (grouping by `iro.type`)
     - Materiality score distribution (statistics from relevant assessment tables)
     - Related ESRS standards (from `iro.esrs_standard`)
     - Topic-specific metrics (if defined in system)


### User Story 11: IRO Database Management
**As an ESG/Sustainability Analyst, I need to maintain the IRO database by updating, consolidating, and organizing IROs so that our sustainability impact data remains accurate and usable**

**Key questions:** 
- Which IROs need updating based on new information or stakeholder feedback?
- How can I consolidate duplicate or related IROs in the system?
- How do I track changes made to IRO documentation over time?

**Info views that might answer these questions:**

1. **Info View: IRO Management Dashboard**
   - **Description:** Central dashboard for managing all IROs with filtering and sorting capabilities
   - **Datapoints needed and table of origin:**
     - IRO listing (from `iro` table joined with `iro_version` table via `current_version_id`)
     - Update status (from `iro` table, `updated_on` field)
     - Stage information (from `iro` table, `current_stage` field)
     - Assessment status (from `iro` table, `last_assessment_date`, `assessment_count` fields)
     - Materiality scores (from `impact_assessment` table, `impact_materiality_score` field)

2. **Info View: IRO Version History**
   - **Description:** Complete history of changes made to a specific IRO
   - **Datapoints needed and table of origin:**
     - IRO versions (from `iro_version` table, filtered by `iro_id`)
     - Version metadata (from `iro_version` table, `version_number`, `created_on`, `created_by` fields)
     - Change details (comparison between versions)
     - Previous version relationships (from `iro_version` table, `parent_version_id` field)

3. **Info View: IRO Relationship Mapper**
   - **Description:** Visual interface for managing relationships between IROs
   - **Datapoints needed and table of origin:**
     - Source and target IROs (from `iro_relationship` table, `source_iro_id` and `target_iro_id` fields)
     - Relationship types (from `iro_relationship` table, `relationship_type` field)
     - Relationship metadata (from `iro_relationship` table, `created_on`, `created_by`, `notes` fields)

**Interaction Requirements:**
- Bulk edit capabilities for updating multiple IROs
- Search functionality with advanced filters
- Mass tagging and categorization tools
- Drag-and-drop relationship mapping
- Change history tracking with diff highlighting
- Warning system for potential data integrity issues

### User Story 12: Value Chain Impact Distribution
**As an ESG/Sustainability Analyst, I need to analyze the distribution of impacts across our value chain so that I can identify hotspots and prioritize interventions**

**Key questions:** 
- Where in our value chain are impacts concentrated?
- Which value chain areas have the highest materiality scores?
- How can I visualize the relationship between value chain position and impact materiality?

**Info views that might answer these questions:**

1. **Info View: Value Chain Distribution Dashboard**
   - **Description:** Visualization of IRO distribution across value chain segments
   - **Datapoints needed and table of origin:**
     - Value chain position data (from `iro_version` table, `value_chain_lv1`, `value_chain_lv2` fields)
     - IRO counts per value chain segment (calculated from `iro_version` table)
     - IRO types by value chain (from `iro` table, `type` field, joined with `iro_version`)
     - Tenant context (from `iro` table, `tenant_id` field)

2. **Info View: Value Chain Materiality Heatmap**
   - **Description:** Heatmap showing materiality scores across value chain segments
   - **Datapoints needed and table of origin:**
     - Value chain position data (from `iro_version` table, `value_chain_lv1`, `value_chain_lv2` fields)
     - Materiality scores (from `impact_assessment` table, `impact_materiality_score` field)
     - IRO type information (from `iro` table, `type` field)
     - Assessment completion data (from `iro` table, `last_assessment_date`)

3. **Info View: Value Chain Segment Detail**
   - **Description:** Detailed analysis of impacts within a specific value chain segment
   - **Datapoints needed and table of origin:**
     - IROs in selected segment (from `iro_version` table filtered by value chain fields)
     - Materiality scores for segment IROs (from `impact_assessment` table)
     - Assessment status (from `iro` table, `current_stage` field)
     - Assessment dates (from `impact_assessment` table, `created_on` field)

**Interaction Requirements:**
- Interactive value chain map with selectable segments
- Filter capability by impact type, materiality threshold, and assessment status
- Toggle between count view and materiality score view
- Drill-down from segment to specific IROs
- Split view to compare upstream, own operations, and downstream impacts
- Export functionality for segment-specific reports

### User Story 13: Assessment Prioritization Dashboard
**As an ESG/Sustainability Analyst, I need a dashboard to prioritize assessment work so that I can focus on the most critical or time-sensitive IROs**

**Key questions:** 
- Which IROs should be prioritized for assessment or reassessment?
- Which IROs have outdated assessments that need refreshing?
- How should I allocate my time across different assessment tasks?

**Info views that might answer these questions:**

1. **Info View: Assessment Priority Queue**
   - **Description:** Prioritized list of IROs requiring assessment attention
   - **Datapoints needed and table of origin:**
     - IRO basic information (from `iro` table joined with `iro_version`)
     - Last assessment date (from `iro` table, `last_assessment_date` field)
     - Current stage (from `iro` table, `current_stage` field)
     - Previous materiality score (from `iro` table, `last_assessment_score` field)
     - Review status (from `review` table, joining on `iro_id`)
     - Age of assessment (calculated from current date and `last_assessment_date`)

2. **Info View: Assessment Workload Planner**
   - **Description:** Tool to plan assessment work across time periods
   - **Datapoints needed and table of origin:**
     - IRO counts by assessment status (calculated from `iro` table)
     - IRO counts by type (from `iro` table, `type` field)
     - Estimated assessment effort (could be stored in configuration or calculated)
     - Due dates or reporting deadlines (would need additional deadline tracking table)

3. **Info View: Review Response Tracker**
   - **Description:** List of assessments with reviewer feedback requiring response
   - **Datapoints needed and table of origin:**
     - Review information (from `review` table)
     - Reviews with 'In_Review' status (from `review` table, `status` field)
     - Review dates (from `review` table, `created_on`, `updated_on` fields)
     - Reviewer information (from `review` table, `reviewer_id` field)
     - IRO information (joining `review` table with `iro` and `iro_version`)

**Interaction Requirements:**
- Drag-and-drop scheduling interface
- Color-coded priority indicators
- Quick filters for different priority factors (age, materiality, review status)
- Personal task assignment and tracking
- Calendar view with assessment deadlines
- Progress tracking for assessment completion targets
