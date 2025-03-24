
# New Home Screen design

## Mapping to Requirements

Below is a summary of how the new home screen addresses key user stories and info views, with a focus on an **integrated experience** that surfaces the most important data up front. The design draws from:

1. **User Story 1 & 2 (ESG/Sustainability Analyst Dashboard)**  
   - Provides a quick overview of IRO distribution, high-level materiality, and direct access to forms/assessments.  
   - Delivers high-priority queues (e.g., for quickly editing impact or financial assessments).

2. **User Story 4 & 6 (IRO Creation and Review/Approval Workflow)**  
   - The homepage includes shortcuts or "task cards" displaying recently created IROs needing additional data or awaiting review.

3. **User Story 10 (Sustainability Topic Analysis)**  
   - Surfaces a simplified "Topic-level" summary on the homepage, reflecting double materiality *only at the topic level* (visual quadrant) and linking to detail pages.

4. **User Story 13 (Assessment Prioritization Dashboard)**  
   - The homepage features an "Assessment Priority" panel or widget summarizing the top items needing attention, capturing the desire for integrated experience in a central "launchpad."

5. **Minimizing Form Fatigue**  
   - Critical fields appear in collapsible or progressive disclosure blocks.  
   - Focus on data that helps them do next-step tasks rather than big static forms.

6. **Handsontable for Quick Edits**  
   - A small "inline table" helps batch-edit or quickly adjust IRO titles, statuses, or materiality scores (where relevant) *without forcing the user into a complex form flow*.

7. **Double Materiality Matrix "Topic View"**  
   - The homepage materiality quadrant specifically accumulates topics at the *topic* level, clarifying that each underlying IRO is only either impact or financial, but the *topic-level* can show the combined "double perspective."

---

## Description

### High-Level Concepts

1. **Prominent Dashboard Metrics**: At the top, four or five large "metric cards" for *Pending Reviews*, *High Materiality Topics*, *Total IROs*, or *Assessments Due*.  
2. **Topic-Level Double Materiality Quadrants**: A simplified quadrant display at the mid-page showing LISTS of topics in each quadrant based on their materiality classification.  
3. **Handsontable "Quick-Edit" Panel**: A short table listing the top 5 or 10 IROs that need immediate attention (e.g., incomplete data, near a deadline). Users can edit certain fields inline.  
4. **Collapsible "Recent Activity"**: A timeline with lightweight lines for newly created or updated IROs, date/time, stage changes, sign-offs, etc.  
5. **Action Cards**: "Add New IRO," "Add New Assessment," or "View Topics," each with minimal friction to get started or to jump into relevant tasks.  

### User Flow Emphases

- **Quickly See 'What to Do Next'?** The top portion is a "Tasks/Re-View" summary to reduce the annoyance of searching for forms.  
- **Topic vs. IRO**: The quadrant displays *topic-level* classifications only, ensuring less confusion about mixing impact vs. financial for a single IRO.
- **Inline Edits**: The central table helps reduce form-based friction by letting the user do minimal, targeted updates. If more detail is needed, they click "Expand" or "Go to Detail."

### Highlights

- **Single-page** that merges key metrics, the double-materiality quadrants, and a short list of "actionable" data with quick edits.  
- Minimizes overwhelming form fields by displaying only the *key columns* in a table. Full forms remain accessible via "Edit" or "Assess" buttons.  
- The quadrant display *only* shows "Topic-level" aggregated data, with a small text note clarifying each underlying IRO is either Impact or Financial.  

---

## ASCII Mockup

Below is a simplified ASCII diagram of the proposed homepage layout. The goal is an **integrated** but *not* hyper-cluttered screen:

```
+------------------------------------------------------------------+
| [Top Navbar: "DMA Platform" | User Info ]                        |
+------------------------------------------------------------------+
| Sidebar          |                MAIN CONTENT (Home Screen)     |
|                  | +------------------------------------------------+
|  - Dashboard     | |  (1) METRIC CARDS ROW (4 boxes)                |
|  - IROs          | |    +----------+   +----------+   +----------+   +-----+ |
|  - Assessments   | |    | Pending  |   |High      |   |Total IROs|   |Topics| |
|  - Reports       | |    | Reviews  |   |Material. |   |          |   |Due   | |
|  - Stakeholders  | +------------------------------------------------+
|                  | +------------------------------------------------+
|                  | |  (2) TOPIC-LEVEL DOUBLE MATERIALITY QUADRANTS  |
|                  | |                                                |
|                  | |   +------------------------+------------------------+
|                  | |   | FINANCIALLY MATERIAL   | DOUBLE MATERIAL        |
|                  | |   | NOT IMPACT MATERIAL    | (IMPACT & FINANCIAL)   |
|                  | |   |                        |                        |
|                  | |   | • Topic 1              | • Topic 5              |
|                  | |   | • Topic 2              | • Topic 6              |
|                  | |   | • Topic 3              | • Topic 7              |
|                  | |   | • Topic 4              | • Topic 8              |
|                  | |   |                        |                        |
|                  | |   +------------------------+------------------------+
|                  | |   | NOT MATERIAL           | IMPACT MATERIAL        |
|                  | |   | (NEITHER)              | NOT FINANCIAL MATERIAL |
|                  | |   |                        |                        |
|                  | |   | • Topic 9              | • Topic 13             |
|                  | |   | • Topic 10             | • Topic 14             |
|                  | |   | • Topic 11             | • Topic 15             |
|                  | |   | • Topic 12             | • Topic 16             |
|                  | |   |                        |                        |
|                  | |   +------------------------+------------------------+
|                  | |                                                |
|                  | +------------------------------------------------+
|                  | +------------------------------------------------+
|                  | | (3) "PRIORITY IROS" QUICK EDIT TABLE (Handsontable) |
|                  | |  +---------------------------------------------+    |
|                  | |  | ID | Title  | Type | Status |   *Key Cols*  |    |
|                  | |  | .. | ...    | ...  | ...    |  inline edit..|    |
|                  | |  +---------------------------------------------+    |
|                  | |   [ Save changes automatically / or Save btn ]      |
|                  | +------------------------------------------------+
|                  | +------------------------------------------------+
|                  | | (4) RECENT ACTIVITY TIMELINE or LIST           |
|                  | |   - Created IRO #1234 ...  [1 hour ago]        |
|                  | |   - Updated "Scope Score" on IRO #1209 [2 days ago] |
|                  | +------------------------------------------------+
+------------------------------------------------------------------+
```

**Key UI Sections**:

1. **Metric Cards Row**: Quick stats (e.g., total IROs, how many are high materiality, how many are pending review, etc.).  
2. **Topic-Level Double Materiality Quadrants**: 
   - Four quadrants clearly displaying topics based on their materiality:
     - Top-Left: Financially Material but Not Impact Material topics
     - Top-Right: Double Material topics (both Impact and Financial)
     - Bottom-Left: Not Material topics (neither Impact nor Financial)
     - Bottom-Right: Impact Material but Not Financially Material topics
   - Each quadrant contains a LIST of topics that fall under that classification
   - Horizontal axis: Impact materiality (left = not material, right = material)
   - Vertical axis: Financial materiality (bottom = not material, top = material)
3. **Handsontable Quick Edit**: A short table listing 5–10 highest-priority or incomplete IROs, letting the user quickly fix a title, reassign a stage, or set a type.  
4. **Recent Activity**: A short feed or timeline, collapsible if desired, so the user sees real-time changes by themselves or others.  

This design respects the constraints about the double-materiality matrix: *only at the topic level* do we show combined classifications. Each IRO stored in the system is distinctly either Impact or Financial. The user can easily see which topics fall into each materiality quadrant.

By integrating these modules on a single screen, **form-filling** friction is minimized—only the crucial, final-level details (like a red-flag IRO) might require the user to jump into a fuller form.  

---


# Steps to implement new home screen 
I'll assess the readiness to revamp the home screen based on the information provided in the files.

## 1) Current State Assessment

Looking at the proposed new home screen design and the existing code, we need to evaluate whether the underlying data structures are in place to support the revamp. Here's my analysis:

### What's Already in Place:
1. **Basic Database Structure**: 
   - The IRO model structure exists with financial and impact assessments
   - Models for topics, relationships, and assessments are defined

2. **Core Functionality**:
   - The ability to fetch IROs across tenants
   - Materiality assessment capabilities
   - Metrics calculations for dashboards
   - Context selection for tenant/assessment/IRO

3. **UI Components**:
   - Handsontable integration for data editing
   - Chart.js for visualization
   - Bootstrap and other styling frameworks
   - Context selection modals

### What's Missing:
1. **Topic-Level Data Aggregation**: 
   - The new design emphasizes topic-level double materiality, but the current code primarily works at the IRO level
   - No clear aggregation functions for grouping IROs by topic into quadrants

2. **Topic Entity**:
   - While there are fields for topics in the IRO models (`sust_topic_level1`, `sust_topic_level2`), there's no dedicated Topic model or way to aggregate IROs at the topic level

3. **Dashboard Components**:
   - No implementation for the "Priority IROs" quick edit table as specified in the design
   - No integrated "Topic-Level Double Materiality Quadrants" view

4. **Data Services**:
   - Missing API endpoints to provide topic-level aggregation data
   - No services to calculate which topics fall into which materiality quadrants

5. **Front-end Components**:
   - Missing UI components for the quadrant view with topic lists
   - No implementation of the collapsible Recent Activity component

## 2) Complete List of Scripts That Need to Be Updated or Created

### Backend Files to Update:
1. **`apps/assessments/models.py`**:
   - Add a dedicated `Topic` model to represent sustainability topics
   - Add relationship between IROs and Topics
   - Add methods to calculate topic-level materiality scores

2. **`apps/assessments/utils.py`**:
   - Add utility functions for topic-level aggregation
   - Create functions to classify topics into materiality quadrants

3. **`apps/assessments/views.py`**:
   - Add view functions to provide topic data for the quadrants
   - Create endpoints for the quick-edit table functionality

4. **`core/views.py`**:
   - Update `home_dashboard` view to include topic-level data
   - Add data processing for materiality quadrants
   - Include high priority IROs for quick editing

5. **`apps/assessments/urls.py`**:
   - Add new URL patterns for topic-related views and APIs

### Frontend Files to Update:
1. **`templates/home.html`**:
   - Complete redesign based on the new mockup
   - Implement the four major sections (metrics, quadrants, quick-edit, recent activity)

2. **`static/js/dashboard.js`**:
   - Add functions to handle the topic-level double materiality quadrants
   - Implement the quick-edit table interaction logic

3. **`static/js/handsontable-manager.js`**:
   - Enhance to support the "Quick-Edit" panel functionality

### New Files to Create:
1. **`apps/assessments/topic_aggregator.py`**:
   - Service for aggregating IROs into topics and calculating topic-level materiality

2. **`static/js/materiality_quadrants.js`**:
   - JavaScript module to handle the rendering and interaction with the quadrant view

3. **`static/js/quick_edit_manager.js`**:
   - JavaScript module for the quick-edit Handsontable functionality

4. **`templates/components/materiality_quadrants.html`**:
   - Component template for the topic-level quadrant display

5. **`templates/components/priority_iros.html`**:
   - Component template for the quick-edit priority IROs

6. **`templates/components/recent_activity.html`**:
   - Component template for the collapsible recent activity section

7. **`apps/assessments/serializers.py`**:
   - Serializers for topic data and aggregated materiality information

8. **`apps/assessments/api/topic_views.py`**:
   - API views for topic-level data

### CSS Files to Update or Create:
1. **`static/css/dashboard.css`**:
   - Add styles for the new quadrant display
   - Style the quick-edit table
   - Implement responsive layouts for the home screen components

### Complete List of APIs to Create:
1. **Topic Materiality API**:
   - `GET /api/topics/materiality/` - Get topic-level materiality data for quadrants
   
2. **Priority IROs API**:
   - `GET /api/iros/priority/` - Get high-priority IROs for quick editing
   - `PATCH /api/iros/batch-update/` - Update multiple IROs at once

3. **Recent Activity API**:
   - `GET /api/activity/recent/` - Get recent activity data

## Conclusion

The current codebase has a solid foundation with the basic data models and frontend infrastructure in place, but significant work is needed to support the new home screen design. The biggest gap is the lack of topic-level aggregation and visualization components. You'll need to create these components from scratch while building on the existing IRO data structure.

Before proceeding with the revamp, I recommend:

1. First implementing the Topic model and aggregation logic
2. Then creating the necessary APIs for topic-level data 
3. Finally, updating the frontend components to support the new design

This approach ensures you'll have all the underlying data structures in place before beginning the UI redesign.