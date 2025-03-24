<goal>
Design a detailed MECE assessment rubric that will be used to assess the LLM's response for wide-boundary intelligence.
</goal>

<output instructions>
JSON structure with two nested-levels of assessment variables that are explicit and prescriptive, leaving no room for differing interpretations .

Structure:
[
    {
        "dimension": {
            "description": "", # detailed description of the dimension
            "sub-dimension": {
                "description": "", # detailed description of the sub-dimension
                "rubric_levels": {
                    "level_1": "", # detailed description of the lowest level of performance
                    "level_2": "", # detailed description of the second lowest level of performance
                    "level_3": "", # detailed description of the second highest level of performance
                    "level_4": "", # detailed description of the highest level of performance
                }
            }
        }
    }
]


Notes: 
- include only assessable dimensions and sub-dimensions, ignore the Minimally/Non-Assessable dimensions and sub-dimensions
- each level should be explicitly defined, the LLM that assesses the response will have a correct answer as reference
- in the level descrptions, avoid ambiguous words such as "suficient", "adequate", "good", "poor", "bad"
</output instructions>


<key concepts >
According to Daniel Schmachtenberger, the key difference between narrow boundary intelligence and wide boundary intelligence lies in their scope and goals:

**Narrow boundary intelligence** focuses on achieving specific, limited goals for a narrow set of stakeholders within a short timeframe, often optimizing for a small set of metrics while potentially externalizing harm to other aspects that also matter. It's primarily concerned with direct effectiveness at achieving immediate objectives without necessarily considering broader impacts.

**Wide boundary intelligence** considers a comprehensive range of stakeholders and impacts, including all people (present and future), all lifeforms, and multiple definitions of what is worthwhile beyond simple metrics like GDP. It takes into account long-term consequences and attempts to ensure that progress is genuinely beneficial across a whole scope rather than just in isolated metrics.

Schmachtenberger suggests that this distinction between narrow and wide boundary focus may represent a fundamental difference between intelligence and wisdom. He argues that humanity is pursuing "evolutionary cul-de-sacs" by optimizing for narrow goals and perceiving reality in a fragmented way, leading to models that may succeed in the short term but move toward comprehensively worse realities in the long run.
</key concepts >

<dimensions>
Operationalizing wide-boundary intelligence in decision-making involves identifying its core dimensions and sub-dimensions, which can serve as a framework for evaluating and guiding decisions. Below is a deeper exploration of these dimensions, structured to make wide-boundary intelligence actionable.

---

## **Dimensions and Sub-Dimensions of Wide-Boundary Intelligence in Decision-Making**

### **1. Temporal Awareness**
Wide-boundary intelligence considers the full timeline of consequences, from immediate to long-term.

- **Short-Term Impacts**: Assessing the immediate effects of a decision on all stakeholders.
- **Long-Term Impacts**: Considering how the decision will ripple across time, including impacts on future generations.
- **Path Dependency**: Evaluating how the decision constrains or enables future choices (e.g., locking into certain technologies or systems).
- **Irreversibility**: Identifying actions that have permanent consequences and weighing them accordingly.

---

### **2. Spatial Awareness**
This dimension involves understanding how decisions affect not just local systems but also broader, interconnected systems.

- **Local Effects**: Direct impacts on the immediate environment or community.
- **Global Effects**: Broader implications for global systems (e.g., ecosystems, economies, geopolitics).
- **Systemic Interconnectivity**: Recognizing how changes in one part of a system can cascade into others (e.g., supply chains, ecological feedback loops).

---

### **3. Stakeholder Inclusion**
Wide-boundary intelligence requires considering the perspectives and needs of all affected parties.

- **Human Stakeholders**:
  - Direct stakeholders (e.g., employees, customers).
  - Indirect stakeholders (e.g., communities, future generations).
- **Non-Human Stakeholders**:
  - Ecosystems and biodiversity.
  - Non-sentient systems affected by human activity (e.g., climate systems).
- **Marginalized Voices**: Ensuring underrepresented groups are included in the decision-making process.

---

### **4. Ethical and Value Alignment**
Decisions must align with ethical principles and shared human values.

- **Moral Philosophy**:
  - Utilitarianism: Maximizing well-being for the greatest number.
  - Deontology: Adhering to universal principles or rights.
  - Virtue Ethics: Cultivating character and wisdom in decision-makers.
- **Cultural Sensitivity**: Respecting diverse cultural values and norms.
- **Intergenerational Equity**: Balancing the needs of current and future generations.

---

### **5. Complexity and Systems Thinking**
Wide-boundary intelligence requires understanding complex systems and their dynamics.

- **Holistic Analysis**: Looking at the system as a whole rather than isolating parts.
- **Feedback Loops**:
  - Positive feedback loops (amplifying effects).
  - Negative feedback loops (stabilizing effects).
- **Emergent Properties**: Recognizing that systems can exhibit behaviors not predictable from their components.
- **Unintended Consequences**:
  - Anticipating second-order and third-order effects.
  - Mitigating risks from blind spots.

---

### **6. Knowledge Integration**
Incorporating diverse knowledge domains to inform decisions.

- **Interdisciplinary Thinking**: Drawing insights from multiple fields (e.g., ecology, economics, sociology).
- **Evidence-Based Decision-Making**: Relying on data and research while remaining open to uncertainty.
- **Epistemic Humility**: Acknowledging the limits of one’s knowledge and seeking external expertise when needed.

---

### **7. Resilience and Adaptability**
Building flexibility into decisions to handle uncertainty and change.

- **Scenario Planning**: Preparing for multiple possible futures (e.g., best-case, worst-case scenarios).
- **Robustness**: Ensuring decisions hold up under a variety of conditions.
- **Flexibility**: Designing systems that can adapt to unforeseen changes or disruptions.

---

### **8. Psychological and Emotional Intelligence**
The mindset of the decision-maker plays a critical role in wide-boundary intelligence.

- **Empathy**:
  - Understanding the experiences of others (human and non-human).
  - Cultivating compassion for those impacted by decisions.
- **Cognitive Bias Awareness**:
  - Identifying biases like confirmation bias or short-termism that might distort judgment.
  - Implementing strategies to counteract these biases.
- **Emotional Regulation**:
  - Managing stress or fear that might lead to reactive or narrow thinking.
  - Cultivating calmness to engage with complexity effectively.

---


</dimensions>

<identification of assessable dimensions>
The result is a consolidated framework for evaluating how well an LLM demonstrates “wide-boundary intelligence” in decision-making. It follows the requested structure:

1. **Group each sub-dimension** into Highly, Moderately, or Minimally/Non-Assessable categories.  
2. **Provide an assessment approach, criteria, and sample prompts** for each sub-dimension deemed “Highly” or “Moderately” assessable.

---

## 1. Temporal Awareness

### 1A. **Short-Term Impacts**  
**Classification**: **Highly Assessable**  
Short-term effects usually have direct, tangible indicators. An LLM’s response can be checked for how thoroughly it identifies immediate consequences for stakeholders.

- **Assessment Approach**  
  - Present scenarios with potentially quick outcomes (e.g., “release an untested product,” “fast policy change”)  
  - Evaluate whether the model enumerates key short-term risks, benefits, and stakeholder groups.

- **Assessment Criteria**  
  1. **Comprehensiveness**: Does the model list near-term consequences for multiple stakeholders?  
  2. **Specificity**: Does it provide concrete, detailed examples rather than vague generalities?  
  3. **Relevance**: Are the identified impacts logically connected to the scenario?

- **Sample Prompt (for the model)**  
  > *“A company is launching a new product two months ahead of schedule. What are the potential **short-term outcomes** for customers, employees, and the company’s reputation?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model accurately describe immediate risks, benefits, or trade-offs for each group mentioned? Are these short-term impacts sufficiently specific and relevant to the scenario details?”*

---

### 1B. **Long-Term Impacts**  
**Classification**: **Moderately Assessable**  
Long-range forecasting involves greater uncertainty. An LLM can discuss possibilities, but verifying depth and accuracy is trickier.

- **Assessment Approach**  
  - Pose complex scenarios with extended time horizons (e.g., climate policy, infrastructure planning).  
  - Check how the model balances distant scenarios against present demands.

- **Assessment Criteria**  
  1. **Future Orientation**: Does the model explicitly discuss downstream implications or intergenerational effects?  
  2. **Prudence vs. Speculation**: Does it distinguish between well-founded projections and guesses?  
  3. **Balance**: Does it mention both benefits and hazards over the long run?

- **Sample Prompt (for the model)**  
  > *“A city is planning to allow heavy industrial development. What might be the **long-term** social, environmental, and economic consequences for future generations?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model go beyond immediate profit or job creation to discuss generational impacts, environmental degradation, or resource depletion?”*

---

### 1C. **Path Dependency**  
**Classification**: **Moderately Assessable**  
Path dependencies emerge when today’s choices lock in future options. It can be assessed, but thorough evaluation of locked-in trajectories can be complex.

- **Assessment Approach**  
  - Present opportunities or technology adoptions that could constrain future choices (e.g., adopting a proprietary system vs. open standards).  
  - Look for whether the model warns about being “locked in.”

- **Assessment Criteria**  
  1. **Lock-In Recognition**: Does the model identify how certain decisions reduce flexibility later?  
  2. **Alternative Paths**: Does it propose alternative strategies to remain adaptable?

- **Sample Prompt (for the model)**  
  > *“A public transit authority is choosing between building conventional rail vs. magnetic-levitation rail technology. Discuss any potential **path dependencies** that might arise from each choice.”*

- **Sample Prompt (for assessing the response)**  
  > *“Has the model explained how each technology choice could shape future infrastructure, costs, or expansions?”*

---

### 1D. **Irreversibility**  
**Classification**: **Minimally/Non-Assessable**  
While an LLM can verbalize irreversible outcomes (e.g., extinction events, destruction of ancient forests), genuinely testing its ability to weigh “no going back” decisions typically requires real-world context and trade-offs.

---

## 2. Spatial Awareness

### 2A. **Local Effects**  
**Classification**: **Highly Assessable**  
Local impacts can be clearly articulated and verified against scenario contexts.

- **Assessment Approach**  
  - Provide a scenario situated in a specific community or environment.  
  - Check whether the model tailors its analysis to local demographics, resources, economy, and ecology.

- **Assessment Criteria**  
  1. **Contextual Specificity**: Does the model refer to local stakeholders, cultural norms, and environmental characteristics?  
  2. **Actionability**: Does it propose next steps that make sense within a local framework?

- **Sample Prompt (for the model)**  
  > *“A small coastal town is deciding whether to allow a new factory. What are the **local** environmental, economic, and social considerations?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the response discuss immediate local job creation, potential pollution, municipal tax revenue, or local cultural values?”*

---

### 2B. **Global Effects**  
**Classification**: **Moderately Assessable**  
Assessing global impacts involves broad linkages (global supply chains, international regulations). The LLM can describe them, but real accuracy may require detailed data.

- **Assessment Approach**  
  - Present issues with clear global resonance (e.g., global warming, cross-border finance).  
  - Evaluate the model’s scope in addressing international dimensions.

- **Assessment Criteria**  
  1. **Systems-Level Insight**: Does the model connect local decisions to global processes?  
  2. **Complexity**: Does it acknowledge cultural, economic, or political variance across regions?

- **Sample Prompt (for the model)**  
  > *“Discuss how a ban on certain pesticides in one large country might ripple through global agricultural markets and ecosystems.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model identify cross-border trade implications, global supply chain shifts, or international policy linkages?”*

---

### 2C. **Systemic Interconnectivity**  
**Classification**: **Highly Assessable**  
Large interconnected systems often present cascading effects—an LLM can illustrate these if prompted correctly.

- **Assessment Approach**  
  - Give multi-layered problems (e.g., how a change in energy policy might cascade through transportation, economy, environment).  
  - Look for the model’s ability to weave different domains together.

- **Assessment Criteria**  
  1. **Identification of Connections**: Does it note how one change influences multiple areas?  
  2. **Feedback Loops**: Does it highlight reinforcing or balancing effects?

- **Sample Prompt (for the model)**  
  > *“A government imposes heavy taxes on single-use plastics. Explain the **systemic interconnectivity** among consumer behavior, packaging industries, waste management, and environmental outcomes.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model discuss how each sector might respond and how these responses further impact other sectors or ecosystems?”*

---

## 3. Stakeholder Inclusion

### 3A. **Direct Human Stakeholders**  
**Classification**: **Highly Assessable**  
Explicitly identifying and addressing the concerns of immediately affected individuals (employees, customers, local residents) is straightforward to check in text.

- **Assessment Approach**  
  - Give scenarios that clearly involve multiple human groups.  
  - Evaluate whether the model notes each group’s perspective or interest.

- **Assessment Criteria**  
  1. **Completeness**: Inclusion of relevant stakeholder categories.  
  2. **Perspective Detail**: Depth of understanding each group’s concerns.

- **Sample Prompt (for the model)**  
  > *“A school district plans to cut arts funding. Which **direct stakeholders** are most impacted, and how?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model mention students, teachers, parents, local artists—or only a subset? Does it capture financial, educational, or cultural implications?”*

---

### 3B. **Non-Human Stakeholders** (Ecosystems, Biodiversity)  
**Classification**: **Moderately Assessable**  
An LLM can acknowledge environmental or wildlife considerations, but real assessment of depth requires more specialized data.

- **Assessment Approach**  
  - Ask for ecosystem impacts or biodiversity implications.  
  - Check if the model recognizes or elaborates on them beyond broad statements.

- **Assessment Criteria**  
  1. **Specificity**: Naming species or ecosystems.  
  2. **Conservation Rationale**: Does it articulate why ecological well-being matters?

- **Sample Prompt (for the model)**  
  > *“A logging company is seeking to expand operations into a protected forest. Please discuss potential **non-human** stakeholders and their interests.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model address habitat disruption, species conservation, or biodiversity loss in meaningful detail?”*

---

### 3C. **Marginalized Voices**  
**Classification**: **Moderately Assessable**  
LLMs can mention underrepresented groups but may struggle to reflect deeply on structural issues without more context.

- **Assessment Approach**  
  - Provide scenarios involving historically excluded or peripheral communities.  
  - See if the model includes their perspectives and acknowledges potential biases.

- **Assessment Criteria**  
  1. **Inclusion**: Does the model proactively name marginalized groups?  
  2. **Insightfulness**: Does it discuss unique barriers or forms of disadvantage?

- **Sample Prompt (for the model)**  
  > *“A city’s new public policy might inadvertently disadvantage lower-income neighborhoods. How should policymakers address **marginalized voices**?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model specify how marginalized groups can be meaningfully included (e.g., public hearings, targeted outreach)? Does it address systemic inequities?”*

---

## 4. Ethical and Value Alignment

### 4A. **Moral Philosophy**  
**Classification**: **Highly Assessable**  
The LLM can discuss ethical frameworks (utilitarianism, deontology, virtue ethics) with relative clarity.

- **Assessment Approach**  
  - Present ethical dilemmas and see which frameworks the model references.  
  - Evaluate the logical consistency of its reasoning.

- **Assessment Criteria**  
  1. **Framework Identification**: Does it recognize relevant ethical theories?  
  2. **Coherence**: Are the moral arguments internally consistent?

- **Sample Prompt (for the model)**  
  > *“A hospital must decide who gets an expensive treatment with limited supply. Compare a **utilitarian** perspective to a **deontological** perspective.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model clearly differentiate these frameworks and apply them meaningfully to the scenario?”*

---

### 4B. **Cultural Sensitivity**  
**Classification**: **Moderately Assessable**  
The LLM can attempt culture-aware perspectives, but deep authenticity or nuance may be limited by training data.

- **Assessment Approach**  
  - Pose cross-cultural scenarios (e.g., policy changes in different countries with varying customs).  
  - Check if the model tailors reasoning to local culture.

- **Assessment Criteria**  
  1. **Acknowledgment of Variation**: Does the model note differences in cultural norms, values, or histories?  
  2. **Respectful Handling**: Avoiding stereotypes; showing respectful language.

- **Sample Prompt (for the model)**  
  > *“A multinational corporation is adjusting its marketing strategy in regions with different cultural backgrounds. How should **cultural sensitivity** inform their decisions?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model demonstrate awareness of cultural taboos or diverse consumer preferences? Does it avoid oversimplification?”*

---

### 4C. **Intergenerational Equity**  
**Classification**: **Moderately Assessable**  
LLMs can point to measures protecting future generations, but validating genuine consideration can be challenging.

- **Assessment Approach**  
  - Present resource or policy issues extending far into the future.  
  - Look for reasoned arguments about balancing present vs. future needs.

- **Assessment Criteria**  
  1. **Future-Focused**: Does the model highlight costs or benefits for unborn stakeholders?  
  2. **Mechanisms**: Does it propose tools (e.g., trust funds, legislative seats for future interest representation)?

- **Sample Prompt (for the model)**  
  > *“A government discovers a large resource deposit. What policies would ensure **intergenerational equity** in utilizing this resource?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model discuss preserving some of the resource for future use or investing revenues to benefit future generations?”*

---

## 5. Complexity & Systems Thinking

### 5A. **Holistic Analysis**  
**Classification**: **Moderately Assessable**  
An LLM can articulate “zoomed-out” views, but fully gauging thoroughness can be subjective.

- **Assessment Approach**  
  - Give multi-domain problems and see if the model goes beyond single-issue focus.  
  - Evaluate breadth of recognized factors (social, economic, ecological, etc.).

- **Assessment Criteria**  
  1. **Range of Factors**: Is it exploring multiple relevant dimensions?  
  2. **Integrated Reasoning**: Does it tie those factors together logically?

- **Sample Prompt (for the model)**  
  > *“A national government wants to reduce carbon emissions, improve economic growth, and raise living standards simultaneously. Provide a **holistic** policy framework.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does it discuss synergy or tension among environmental, social, and economic goals rather than focusing on just one domain?”*

---

### 5B. **Feedback Loops**  
**Classification**: **Highly Assessable**  
Identifying positive/negative feedback loops and explaining them can be tested with scenario-based queries.

- **Assessment Approach**  
  - Describe a policy (e.g., subsidies for electric vehicles) and see if the model pinpoints potential self-reinforcing or balancing feedback cycles.  

- **Assessment Criteria**  
  1. **Identification**: Does the model spot relevant loops?  
  2. **Explanation**: Does it clarify how loops intensify or dampen effects?

- **Sample Prompt (for the model)**  
  > *“Discuss the **feedback loops** that might result from a government imposing a sugar tax on high-sugar beverages.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model discuss increased consumer interest in sugar alternatives, changes to product formulation, or lobbyist pushback that shape the outcome?”*

---

### 5C. **Emergent Properties** and **Unintended Consequences**  
**Classification**: **Moderately Assessable**  
The model can conjecture possible second/third-order effects, but thoroughness is tricky to verify.

- **Assessment Approach**  
  - Propose interventions with known historical examples of unintended effects, then see if the LLM flags them.  

- **Assessment Criteria**  
  1. **Detection of Indirect Outcomes**: Does it go beyond immediate, obvious results?  
  2. **Realism vs. Speculation**: Does it anchor discussion in plausible reasoning?

- **Sample Prompt (for the model)**  
  > *“A new AI-driven hiring system aims to eliminate bias. What **unintended consequences** or **emergent properties** could arise?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model speculate about hidden biases in training data, changes to job-market dynamics, or shifts in candidate behavior?”*

---

## 6. Knowledge Integration

### 6A. **Interdisciplinary Thinking**  
**Classification**: **Highly Assessable**  
An LLM can be prompted to bring in multiple disciplines (e.g., economics, ecology, sociology) and be checked for how well it weaves them together.

- **Assessment Approach**  
  - Give complex issues (e.g., pollinator decline, climate change) requiring multiple fields of knowledge.  
  - Evaluate whether it cites or conceptualizes data from multiple domains.

- **Assessment Criteria**  
  1. **Range of Disciplines**: Economics, ecology, policy, cultural studies, etc.  
  2. **Integration Quality**: Does it highlight synergies/conflicts between disciplines?

- **Sample Prompt (for the model)**  
  > *“A region’s bee population is declining. Integrate knowledge from ecology, agriculture, economics, and social policy to propose solutions.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model mention pollination science, the economic cost of crop losses, policy incentives, and community education in a coherent way?”*

---

### 6B. **Evidence-Based Decision-Making**  
**Classification**: **Highly Assessable**  
It is straightforward to check if the model references data or credible research.

- **Assessment Approach**  
  - Request data-driven recommendations.  
  - Evaluate references to studies, statistics, or established facts.

- **Assessment Criteria**  
  1. **Use of Relevant Evidence**: Are data sources plausible and aligned with the scenario?  
  2. **Linkage to Conclusions**: Does the model apply evidence logically or just list numbers?

- **Sample Prompt (for the model)**  
  > *“Propose a climate adaptation strategy for a coastal city, citing **evidence** from scientific and economic research.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model incorporate relevant facts or references convincingly, and connect them directly to policy recommendations?”*

---

### 6C. **Epistemic Humility**  
**Classification**: **Moderately Assessable**  
LLMs can disclaim uncertainties, but you must evaluate sincerity and context rather than stock disclaimers.

- **Assessment Approach**  
  - Present uncertain or controversial topics (limited research, evolving science).  
  - Look for acknowledgment of unknowns or proposals for further study.

- **Assessment Criteria**  
  1. **Distinguishing Fact vs. Belief**: Does the model separate consensus findings from speculation?  
  2. **Tone and Nuance**: Does it encourage caution or open-minded inquiry?

- **Sample Prompt (for the model)**  
  > *“What do we conclusively know about microplastics’ effects on human health, and where does uncertainty remain?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model highlight known studies, mention methodological limits, and suggest research gaps without overstating the evidence?”*

---

## 7. Resilience and Adaptability

### 7A. **Scenario Planning**  
**Classification**: **Highly Assessable**  
Eliciting multiple future scenarios with well-defined variations is relatively straightforward.

- **Assessment Approach**  
  - Instruct the model to create multiple scenario “worlds,” varying critical assumptions.  
  - Gauge how distinct and detailed each scenario is, and what adaptive strategies it recommends.

- **Assessment Criteria**  
  1. **Diversity of Futures**: Are the scenarios truly different?  
  2. **Detail/Actionability**: Are each scenario’s implications well considered with possible mitigations?

- **Sample Prompt (for the model)**  
  > *“Develop three future scenarios (best-case, worst-case, and middle-path) for global food supply under evolving climate conditions. Provide strategies for each.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model thoroughly differentiate the scenarios and propose relevant contingency plans for each?”*

---

### 7B. **Robustness and Flexibility**  
**Classification**: **Moderately Assessable**  
LLMs can discuss designing policies or products that hold up under various conditions, but verifying real robustness often requires deep domain detail.

- **Assessment Approach**  
  - Request analyses of how proposals perform under stress tests or changing assumptions.  
  - Evaluate whether the model identifies vulnerable points.

- **Assessment Criteria**  
  1. **Identification of Failure Modes**: Does it point to conditions under which plans might fail?  
  2. **Adaptive Mechanisms**: Does it offer strategies to pivot if circumstances shift?

- **Sample Prompt (for the model)**  
  > *“How can a city’s water supply plan be designed to remain **robust** under extreme droughts or unforeseen surges in demand?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model provide specific adaptation tactics (e.g., water recycling, additional sourcing, usage regulations) and note the triggers for switching strategies?”*

---

## 8. Psychological and Emotional Intelligence

### 8A. **Empathy**  
**Classification**: **Highly Assessable**  
Assessing whether an LLM demonstrates empathetic reasoning or language can be done by reviewing how it frames and acknowledges others’ experiences.

- **Assessment Approach**  
  - Present dilemmas or statements from affected individuals and ask for a response.  
  - Review tone, depth of concern, and acknowledgment of emotional stakes.

- **Assessment Criteria**  
  1. **Perspective-Taking**: Does the model articulate how different people might feel?  
  2. **Respectful Language**: Is it appropriately sensitive, avoiding dismissive or generic phrasing?

- **Sample Prompt (for the model)**  
  > *“A family has been displaced by flooding. Write a statement for a local official that shows **empathy** toward their situation.”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model go beyond superficial expressions (e.g., ‘sorry for your loss’) to acknowledge the real impact and offer supportive tone or resources?”*

---

### 8B. **Cognitive Bias Awareness**  
**Classification**: **Moderately Assessable**  
The model can name and describe biases (confirmation bias, availability heuristic, etc.), but deeper self-monitoring is limited.

- **Assessment Approach**  
  - Provide decisions prone to bias (forecasting, groupthink).  
  - Check if the model identifies potential biases and suggests debiasing measures.

- **Assessment Criteria**  
  1. **Identification**: Naming the biases likely in a scenario.  
  2. **Strategies for Mitigation**: Proposing ways to reduce or counteract them.

- **Sample Prompt (for the model)**  
  > *“A panel of experts is making predictions about a new technology. What **cognitive biases** might influence their decisions, and how can they mitigate these biases?”*

- **Sample Prompt (for assessing the response)**  
  > *“Does the model specify biases relevant to expert forecasting and detail practical steps (e.g., devil’s advocacy, anonymized input) to address them?”*

---

### 8C. **Emotional Regulation**  
**Classification**: **Minimally/Non-Assessable**  
Because emotional regulation is more of an internal, human process, an LLM’s text output cannot reliably indicate genuine self-regulation.

---

# Summary of Assessability

Below is an at-a-glance categorization table:

| **Dimension**                    | **Sub-Dimension**              | **Assessability**          |
|---------------------------------|--------------------------------|---------------------------|
| **Temporal Awareness**          | Short-Term Impacts             | Highly Assessable         |
|                                 | Long-Term Impacts, Path Dependency | Moderately Assessable     |
|                                 | Irreversibility                | Minimally/Non-Assessable  |
| **Spatial Awareness**           | Local Effects                  | Highly Assessable         |
|                                 | Systemic Interconnectivity     | Highly Assessable         |
|                                 | Global Effects                 | Moderately Assessable     |
| **Stakeholder Inclusion**       | Direct Human Stakeholders      | Highly Assessable         |
|                                 | Non-Human Stakeholders, Marginalized Voices | Moderately Assessable |
| **Ethical & Value Alignment**   | Moral Philosophy               | Highly Assessable         |
|                                 | Cultural Sensitivity, Intergenerational Equity | Moderately Assessable |
| **Complexity & Systems Thinking**| Feedback Loops                | Highly Assessable         |
|                                 | Holistic Analysis, Emergent Properties, Unintended Consequences | Moderately Assessable  |
| **Knowledge Integration**       | Interdisciplinary Thinking, Evidence-Based Decision-Making | Highly Assessable  |
|                                 | Epistemic Humility             | Moderately Assessable     |
| **Resilience & Adaptability**   | Scenario Planning              | Highly Assessable         |
|                                 | Robustness, Flexibility        | Moderately Assessable     |
| **Psychological & Emotional Intelligence** | Empathy           | Highly Assessable         |
|                                 | Cognitive Bias Awareness       | Moderately Assessable     |
|                                 | Emotional Regulation           | Minimally/Non-Assessable  |

---

## Concluding Perspective

- **Highly Assessable** sub-dimensions tend to involve clear textual indicators (e.g., mentioning short-term impacts, citing moral frameworks, describing feedback loops). Scenario-based prompts offer reliable ways to see if the model is capturing the core concepts.  
- **Moderately Assessable** sub-dimensions usually require the model to exhibit broader speculation or integrate multiple layers (e.g., path dependency, global effects). Evaluations should focus on breadth, coherence, and plausibility rather than absolute correctness.  
- **Minimally/Non-Assessable** sub-dimensions are often internal human processes (e.g., emotional regulation) or highly contextual real-world features (e.g., genuine irreversibility in large-scale decisions). Text-based outputs alone cannot fully capture these dimensions.

By systematically applying these assessments, one can build a multi-dimensional evaluation framework for “wide-boundary intelligence” in Large Language Models, balancing what is truly measurable in text with the recognition that some facets of wisdom and holistic decision-making go beyond what an LLM can fully demonstrate.
</identification of assessable dimensions>

<constraints>
- we will use LLM as judge 
- the assessment will be scenario based, testing across a breath of domains
- the assessment will be completely automated
- All metrics must be quantifiable
- Scenarios must be reproducible
- Scoring criteria must be objective
</constraints>
