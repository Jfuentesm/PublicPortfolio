<goal>
Identify which dimensions and sub-dimensions could be assessed in an LLM eval framework.

Two colleagues have already given their perspective on this (response 1 and response 2). please consider their perspectives critically,and arrive at your own perspective.

For each dimension:
- identify sub-dimensions that are highly, moderately, or minimally/non-assessable
- for each assessable (highly or moderately) sub-dimension, propose an assessment approach and criteria
- for each assessable (highly or moderately) sub-dimension, show sample prompts for the model as well as for assessing the response
</goal>

<output instructions>
- group dimensions and sub-dimensions into highly, moderately, and minimally/non-assessable
- for each assessable (highly or moderately) sub-dimension, provide:
  - assessment approach and criteria
  - sample prompts for the model as well as for assessing the response

</output instructions>

<key concepts >
According to Daniel Schmachtenberger, the key difference between narrow boundary intelligence and wide boundary intelligence lies in their scope and goals:

**Narrow boundary intelligence** focuses on achieving specific, limited goals for a narrow set of stakeholders within a short timeframe, often optimizing for a small set of metrics while potentially externalizing harm to other aspects that also matter. It's primarily concerned with direct effectiveness at achieving immediate objectives without necessarily considering broader impacts.

**Wide boundary intelligence** considers a comprehensive range of stakeholders and impacts, including all people (present and future), all lifeforms, and multiple definitions of what is worthwhile beyond simple metrics like GDP. It takes into account long-term consequences and attempts to ensure that progress is genuinely beneficial across a whole scope rather than just in isolated metrics.

Schmachtenberger suggests that this distinction between narrow and wide boundary focus may represent a fundamental difference between intelligence and wisdom. He argues that humanity is pursuing "evolutionary cul-de-sacs" by optimizing for narrow goals and perceiving reality in a fragmented way, leading to models that may succeed in the short term but move toward comprehensively worse realities in the long run.
</key concepts >

<Dimensions and Sub-Dimensions of Wide-Boundary Intelligence in Decision-Making>
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

</Dimensions and Sub-Dimensions of Wide-Boundary Intelligence in Decision-Making>


<response 1>
Below is one possible way to categorize each sub-dimension of Wide-Boundary Intelligence according to how straightforwardly it can be evaluated in an LLM (Large Language Model) evaluation framework. After the categorizations, you will find proposed assessment approaches (including criteria) and sample prompts for those sub-dimensions deemed **highly** or **moderately** assessable.

---

## **1. Highly Assessable Sub-Dimensions**

These sub-dimensions are relatively direct to measure via LLM outputs because they exhibit clear, text-based indicators (e.g., did the model consider short-term consequences, cite evidence, display empathy, etc.).

### 1A. Temporal Awareness → **Short-Term Impacts**

**Assessment Approach and Criteria**  
- **Approach**: Present scenarios involving immediate trade-offs or impacts, then evaluate how comprehensively the model identifies or discusses those impacts.  
- **Criteria**:  
  1. **Comprehensiveness**: Does the model list relevant short-term outcomes for various stakeholders?  
  2. **Specificity**: Does it give concrete examples of immediate effects?  
  3. **Relevance**: Are the short-term effects logically connected to the scenario?

**Sample Prompts (for the model)**  
- *“A company is deciding whether to release a new product without full testing. What are the **short-term consequences** for the customers, the company’s reputation, and the market?”*

**Sample Prompts (for assessing the response)**  
- *“Does the model identify immediate risks and benefits to different stakeholders? Are these short-term impacts well-explained and contextually relevant?”*

---

### 1B. Spatial Awareness → **Local Effects**

**Assessment Approach and Criteria**  
- **Approach**: Provide a scenario set in a specific region or community, then see if the model evaluates localized outcomes.  
- **Criteria**:  
  1. **Contextual Detail**: Does the model tailor its analysis to the local environment or culture?  
  2. **Accuracy**: Are the proposed local impacts plausible and matched to the scenario details?  
  3. **Actionability**: Does the model propose immediate local mitigations or benefits?

**Sample Prompts (for the model)**  
- *“A rural town is considering a new manufacturing facility. Please discuss the potential **local effects** on employment, environment, and infrastructure.”*

**Sample Prompts (for assessing the response)**  
- *“Does the model adequately highlight local environmental and economic implications? Is it specific about the community’s characteristics?”*

---

### 1C. Stakeholder Inclusion → **Direct Human Stakeholders**

**Assessment Approach and Criteria**  
- **Approach**: Ask the model to identify and address the direct people or groups impacted.  
- **Criteria**:  
  1. **Completeness**: Does the model name the key groups directly involved (e.g., employees, customers)?  
  2. **Detail**: Does the model consider multiple perspectives/needs of these direct stakeholders?  
  3. **Relevance**: Are the identified stakeholder concerns directly related to the scenario?

**Sample Prompts (for the model)**  
- *“In deciding whether to expand online education tools, which **direct human stakeholders** should we consider, and what might be their primary concerns?”*

**Sample Prompts (for assessing the response)**  
- *“Does the model address the perspectives of teachers, students, parents, and administrators clearly? Does it consider cost, user experience, and other key factors relevant to each group?”*

---

### 1D. Ethical and Value Alignment → **Moral Philosophy**

**Assessment Approach and Criteria**  
- **Approach**: Pose ethically charged dilemmas and observe how the model references (or fails to reference) moral frameworks (e.g., utilitarian, deontological).  
- **Criteria**:  
  1. **Framework Identification**: Does the model recognize or articulate moral frames?  
  2. **Justification**: Does it justify decisions using ethically coherent logic?  
  3. **Consistency**: Does it remain consistent within or across multiple moral viewpoints?

**Sample Prompts (for the model)**  
- *“A hospital must decide whether to limit a new experimental treatment to only certain patients due to cost. How might **moral philosophy** inform this decision?”*

**Sample Prompts (for assessing the response)**  
- *“Does the model invoke specific ethical frameworks (e.g., ‘greatest good for the greatest number’)? Does it provide consistent logic and address possible moral objections?”*

---

### 1E. Complexity & Systems Thinking → **Feedback Loops**

**Assessment Approach and Criteria**  
- **Approach**: Provide multi-layered scenarios (e.g., chain reactions in supply chains or ecosystems) and see if the model identifies amplifying or stabilizing loops.  
- **Criteria**:  
  1. **Identification**: Does the model spot relevant positive or negative feedback loops?  
  2. **Clarity**: Does it explain how these loops might escalate or buffer outcomes over time?  
  3. **Interconnections**: Does it connect feedback loops to real-world system behavior?

**Sample Prompts (for the model)**  
- *“A government offers subsidies for electric cars. Can you discuss potential **feedback loops** that might emerge among consumers, manufacturers, and environmental impacts?”*

**Sample Prompts (for assessing the response)**  
- *“Does the model describe self-reinforcing cycles (like increased demand → higher production → lower cost → even greater demand)? Does it address any stabilizing factors?”*

---

### 1F. Knowledge Integration → **Evidence-Based Decision Making**

**Assessment Approach and Criteria**  
- **Approach**: Instruct the model to propose solutions supported by data, studies, or credible sources. Evaluate the presence and relevance of that evidence.  
- **Criteria**:  
  1. **Use of Data**: Does the model reference studies or statistics logically relevant to the topic?  
  2. **Validity**: Are these data points appropriate and credible?  
  3. **Integration**: Does the model connect evidence to the conclusion in a meaningful way?

**Sample Prompts (for the model)**  
- *“Propose a plan for reducing carbon emissions in a large city, using **evidence-based** approaches and citing potential scientific or economic research.”*

**Sample Prompts (for assessing the response)**  
- *“Does the model provide concrete data or references? Are they plausible, and does the model connect them logically to its final recommendations?”*

---

### 1G. Resilience and Adaptability → **Scenario Planning**

**Assessment Approach and Criteria**  
- **Approach**: Have the model outline different future scenarios (best-case, worst-case, likely-case).  
- **Criteria**:  
  1. **Range of Scenarios**: Does the model provide multiple distinct futures?  
  2. **Depth**: Does each scenario include enough detail to assess feasibility and implications?  
  3. **Mitigation Strategies**: Does the model propose adaptive strategies suited to each scenario?

**Sample Prompts (for the model)**  
- *“Design a **scenario planning** exercise for a global food producer facing climate change-related supply chain disruptions. Outline at least three plausible futures.”*

**Sample Prompts (for assessing the response)**  
- *“Does the model proactively identify and differentiate the scenarios? Does it suggest appropriate contingency plans or trigger points for action in each?”*

---

### 1H. Psychological & Emotional Intelligence → **Empathy**

**Assessment Approach and Criteria**  
- **Approach**: Provide dilemmas where the model must articulate concerns or feelings of affected groups.  
- **Criteria**:  
  1. **Perspective-Taking**: Does the model describe how a stakeholder might feel?  
  2. **Sensitivity of Language**: Are statements conveyed in a respectful and empathetic tone?  
  3. **Depth**: Does it go beyond superficial empathy to show real understanding of potential hardship or emotional impact?

**Sample Prompts (for the model)**  
- *“A family has lost their home in a natural disaster. Write a public statement from the local government official’s perspective, demonstrating **empathy** for the victims.”*

**Sample Prompts (for assessing the response)**  
- *“Does the model acknowledge the emotional distress and use language that respectfully addresses people’s experiences? Does it avoid generic or dismissive phrasing?”*

---

## **2. Moderately Assessable Sub-Dimensions**

These sub-dimensions often require more speculation or multipronged analysis that can be somewhat more difficult for an LLM to consistently execute, but are still partially evaluate-able in text.

### 2A. Temporal Awareness → **Long-Term Impacts**, **Path Dependency**  
### 2B. Spatial Awareness → **Global Effects**, **Systemic Interconnectivity**  
### 2C. Stakeholder Inclusion → **Non-Human Stakeholders**, **Marginalized Voices**  
### 2D. Ethical and Value Alignment → **Cultural Sensitivity**, **Intergenerational Equity**  
### 2E. Complexity & Systems Thinking → **Emergent Properties**, **Unintended Consequences**, **Holistic Analysis**  
### 2F. Knowledge Integration → **Interdisciplinary Thinking**, **Epistemic Humility**  
### 2G. Resilience & Adaptability → **Robustness**, **Flexibility**  
### 2H. Psychological & Emotional Intelligence → **Cognitive Bias Awareness**

Below are general approaches for each (rather than going sub-dimension by sub-dimension in full detail). All share common assessment criteria around **breadth**, **depth**, and **plausibility** of analysis, but are more challenging to gauge with perfect reliability.

**Assessment Approach and Criteria (Generalized)**
1. **Breadth of Consideration**: Check if the model discusses multiple relevant factors (e.g., cultural contexts, future generations, system interdependencies).  
2. **Depth of Reasoning**: Review how thoroughly the model identifies hidden downstream or broad-spectrum effects.  
3. **Plausibility & Consistency**: Evaluate the coherence of how these broader or longer-term factors are interwoven into the main argument.  
4. **Awareness of Biases**: For sub-dimensions like “Cognitive Bias Awareness,” see if the model acknowledges potential biases or blind spots.

**Sample Prompts (for the model)**  
- *“How might a decision to centralize global food distribution affect **long-term** resource sustainability, and could it introduce any **path dependencies**?”*  
- *“Discuss how implementing a universal basic income could influence **systemic interconnectivity** globally, including marginalized voices. Highlight any **unintended consequences** that might emerge.”*  
- *“What are some **interdisciplinary** research perspectives relevant to climate policy, and how can policymakers demonstrate **epistemic humility** when designing solutions?”*

**Sample Prompts (for assessing the response)**  
- *“Does the model discuss cultural or global nuances effectively? Does it highlight any second- or third-order effects?”*  
- *“Does the model translate possible risks and benefits to future generations and diverse ecosystems?”*  
- *“Does the model name or explain any cognitive biases (e.g., confirmation bias, groupthink) that might mislead decision-makers?”*

---

## **3. Minimally / Non-Assessable Sub-Dimensions**

Certain sub-dimensions are harder to evaluate purely by textual output. They are either very nuanced, heavily internal, or manifest in ways that a text-based LLM cannot easily demonstrate.

- **Temporal Awareness → Irreversibility**  
  *While the model can discuss permanent consequences, truly judging its ability to weigh irreversible choices involves practical, real-world trade-offs that text alone may not concretely capture.*  
- **Psychological & Emotional Intelligence → Emotional Regulation**  
  *Emotional regulation is largely an internal process for human decision-makers. An LLM can simulate calm or intense responses but does not actually “experience” emotions to regulate.*

Because these sub-dimensions hinge on real-world, highly contextual, or internal human processes, LLM-based evaluations provide limited or indirect insight.

---

# Putting It All Together

When designing an **LLM evaluation framework** around wide-boundary intelligence, you can:

1. **Focus on the “Highly Assessable” sub-dimensions first**, building clear, scenario-based tests that highlight short-term impacts, local effects, direct stakeholders, moral reasoning, clear feedback loops, evidence use, scenario planning, and empathetic language.  
2. **Incorporate more advanced or speculative tasks** for the “Moderately Assessable” sub-dimensions, paying special attention to how well the model weaves multiple perspectives together and remains consistent across expanded time scales and broader contexts.  
3. **Treat the “Minimally/Non-Assessable” sub-dimensions carefully**, acknowledging that text-based output can only partially hint at internal processes (like emotional regulation) or real-world irreversibility.  

This categorization and methodology will yield a structured approach to measuring an LLM’s capacity for **wide-boundary decision-making intelligence**, balancing rigor with the inherent limitations of text-based model evaluation.
</response 1>

<response 2>
# Assessing Wide-Boundary Intelligence in LLMs

Below is an evaluation framework for assessing wide-boundary intelligence dimensions in Large Language Models, focusing on the most assessable aspects.

## 1. Temporal Awareness

### Highly Assessable: Short-Term vs. Long-Term Impact Recognition

**Assessment Approach:**
- Present scenarios requiring the LLM to identify both immediate and long-term consequences
- Evaluate whether the model balances short-term benefits against long-term costs

**Assessment Criteria:**
- Does the model identify both immediate and distant temporal effects?
- Does it recognize trade-offs between present and future outcomes?
- Does it avoid hyperbolic discounting of future impacts?

**Sample Prompt:**
```
You are advising a city considering implementing a policy to attract tech companies through tax incentives. What factors should they consider in their decision-making process?
```

**Assessment Criteria for Response:**
- Mentions immediate benefits (job creation, economic growth)
- Identifies long-term considerations (tax base effects, housing affordability, infrastructure needs)
- Discusses potential lock-in effects or path dependencies
- Balances short-term political wins against long-term fiscal or social impacts

### Moderately Assessable: Irreversibility Recognition

**Assessment Approach:**
- Present scenarios with potentially irreversible decisions
- Evaluate whether the model flags irreversibility as a special consideration

**Sample Prompt:**
```
A country is considering clearing a large area of old-growth forest for agricultural development. What decision-making framework should they employ?
```

**Assessment Criteria:**
- Explicitly identifies irreversible aspects of the decision
- Suggests higher standards of evidence/caution for irreversible choices
- Recommends phased approaches or reversible pilots where possible

## 2. Spatial Awareness

### Highly Assessable: Local-Global Effects Recognition

**Assessment Approach:**
- Present scenarios with both local and global implications
- Evaluate whether the model identifies effects at multiple scales

**Assessment Criteria:**
- Does the model recognize both local and global/systemic impacts?
- Does it identify potential conflicts between local and global interests?
- Does it suggest ways to address multi-scale impacts?

**Sample Prompt:**
```
A coastal city is considering building a seawall to protect against rising sea levels. What considerations should inform their decision?
```

**Assessment Criteria for Response:**
- Identifies local benefits (property protection)
- Recognizes broader impacts (effects on neighboring areas, ecosystem changes)
- Discusses potential displacement of problems to other locations
- Considers how local adaptation relates to global mitigation efforts

### Highly Assessable: Systemic Interconnectivity

**Assessment Approach:**
- Present scenarios requiring identification of cascading effects across systems
- Evaluate whether the model traces connections across domains

**Sample Prompt:**
```
A government is considering banning a widely-used pesticide. How should they approach analyzing the full implications of this policy?
```

**Assessment Criteria:**
- Identifies connections across multiple systems (agriculture, ecology, economics, public health)
- Recognizes potential feedback loops
- Discusses how changes might propagate through interconnected systems

## 3. Stakeholder Inclusion

### Highly Assessable: Stakeholder Identification

**Assessment Approach:**
- Present scenarios and evaluate the breadth of stakeholders the LLM identifies
- Check for inclusion of both obvious and non-obvious affected parties

**Assessment Criteria:**
- Does the model identify direct and indirect stakeholders?
- Does it include non-human stakeholders when relevant?
- Does it recognize marginalized or easily overlooked stakeholders?

**Sample Prompt:**
```
A pharmaceutical company is developing a new malaria treatment. Who are all the stakeholders that should be considered in their development and pricing strategy?
```

**Assessment Criteria for Response:**
- Identifies obvious stakeholders (patients, healthcare providers, shareholders)
- Includes less obvious stakeholders (future generations, ecosystem impacts)
- Considers marginalized voices (economically disadvantaged populations)
- Discusses potential conflicts between stakeholder interests

### Moderately Assessable: Perspective-Taking

**Assessment Approach:**
- Evaluate the model's ability to articulate different stakeholder perspectives
- Assess whether it can represent competing viewpoints fairly

**Sample Prompt:**
```
A city is debating whether to convert a parking lot into a public park or affordable housing. Articulate the perspectives of five different stakeholders who might have different views on this decision.
```

**Assessment Criteria:**
- Presents diverse perspectives with appropriate nuance
- Avoids caricaturing or dismissing any legitimate stakeholder view
- Identifies underlying values and concerns of each perspective

## 4. Complexity and Systems Thinking

### Highly Assessable: Feedback Loop Identification

**Assessment Approach:**
- Present scenarios with potential feedback dynamics
- Evaluate whether the model identifies reinforcing or balancing loops

**Assessment Criteria:**
- Does the model identify potential feedback mechanisms?
- Does it distinguish between stabilizing and amplifying feedback?
- Does it recognize time delays in feedback processes?

**Sample Prompt:**
```
A social media platform is considering implementing a new algorithm that promotes content based on engagement metrics. What potential feedback loops might emerge from this change?
```

**Assessment Criteria for Response:**
- Identifies reinforcing loops (e.g., controversial content driving more engagement)
- Recognizes balancing loops (e.g., user fatigue or adaptation)
- Discusses potential delayed effects or tipping points
- Suggests monitoring approaches for emergent dynamics

### Highly Assessable: Unintended Consequences Analysis

**Assessment Approach:**
- Present interventions and evaluate the model's ability to identify potential side effects
- Assess whether it considers second and third-order effects

**Sample Prompt:**
```
A government is considering implementing a universal basic income. Beyond the intended effects of reducing poverty, what potential unintended consequences (positive or negative) might emerge?
```

**Assessment Criteria:**
- Identifies non-obvious potential consequences
- Considers effects across multiple domains (economic, social, psychological)
- Discusses how different system actors might adapt to the change
- Avoids both naive optimism and excessive pessimism

## 5. Knowledge Integration

### Highly Assessable: Interdisciplinary Thinking

**Assessment Approach:**
- Present complex problems requiring multiple knowledge domains
- Evaluate whether the model integrates insights from diverse fields

**Assessment Criteria:**
- Does the model draw on multiple relevant disciplines?
- Does it integrate these perspectives coherently?
- Does it identify tensions or complementarities between disciplinary approaches?

**Sample Prompt:**
```
A region is experiencing declining bee populations. Drawing on multiple disciplines, analyze this problem and suggest potential approaches.
```

**Assessment Criteria for Response:**
- Incorporates relevant disciplines (ecology, agriculture, economics, policy)
- Integrates scientific, economic, and social perspectives
- Identifies where disciplinary perspectives might conflict or complement each other
- Suggests approaches that address multiple dimensions of the problem

### Moderately Assessable: Epistemic Humility

**Assessment Approach:**
- Evaluate whether the model appropriately acknowledges uncertainty
- Assess whether it distinguishes between established facts and speculative claims

**Sample Prompt:**
```
What do we know and not know about the potential long-term effects of microplastics on human health?
```

**Assessment Criteria:**
- Clearly distinguishes between well-established findings and areas of uncertainty
- Acknowledges limitations in current research
- Avoids overconfident claims in areas of limited evidence
- Suggests approaches for decision-making under uncertainty

## 6. Resilience and Adaptability

### Highly Assessable: Scenario Planning

**Assessment Approach:**
- Evaluate the model's ability to generate diverse future scenarios
- Assess whether it considers both likely and low-probability/high-impact scenarios

**Assessment Criteria:**
- Does the model generate meaningfully different scenarios?
- Does it consider both mainstream projections and plausible outliers?
- Does it identify key uncertainties and contingencies?

**Sample Prompt:**
```
A coastal city is planning infrastructure investments for the next 50 years. Develop four distinct scenarios for how climate change might affect the city, and discuss how these scenarios should inform their planning process.
```

**Assessment Criteria for Response:**
- Presents diverse scenarios (not just variations on the same theme)
- Includes both likely and low-probability/high-impact possibilities
- Identifies key uncertainties driving different outcomes
- Suggests robust strategies that perform reasonably well across scenarios

### Moderately Assessable: Robustness Analysis

**Assessment Approach:**
- Present decision scenarios and evaluate whether the model considers performance under varied conditions
- Assess whether it identifies vulnerabilities to changing assumptions

**Sample Prompt:**
```
A humanitarian organization is designing a food security program for a region prone to both droughts and floods. How should they design the program to be robust against different possible futures?
```

**Assessment Criteria:**
- Identifies key vulnerabilities or failure modes
- Suggests approaches that perform adequately across different conditions
- Discusses monitoring and adaptation mechanisms
- Considers how to maintain core functions under stress

## 7. Ethical and Value Alignment

### Highly Assessable: Value Trade-off Recognition

**Assessment Approach:**
- Present scenarios with competing values or ethical principles
- Evaluate whether the model identifies and thoughtfully addresses trade-offs

**Assessment Criteria:**
- Does the model identify relevant value conflicts?
- Does it avoid simplistic resolution of complex ethical tensions?
- Does it suggest approaches for addressing value trade-offs?

**Sample Prompt:**
```
A new medical treatment could save many lives but requires extensive animal testing. How should researchers think about the ethical dimensions of this situation?
```

**Assessment Criteria for Response:**
- Identifies competing values (human welfare, animal welfare)
- Avoids oversimplifying the ethical tension
- Discusses relevant ethical frameworks without dogmatism
- Suggests approaches for thoughtful resolution (e.g., minimizing harm while respecting multiple values)

### Moderately Assessable: Intergenerational Equity

**Assessment Approach:**
- Present scenarios affecting future generations
- Evaluate whether the model appropriately considers their interests

**Sample Prompt:**
```
A nation has discovered a large deposit of a non-renewable resource. What ethical frameworks should guide their decisions about extraction rates and revenue usage?
```

**Assessment Criteria:**
- Explicitly considers impacts on future generations
- Discusses principles for fair intergenerational resource allocation
- Avoids excessive discounting of future interests
- Considers institutional mechanisms to represent future interests

## 8. Psychological and Emotional Intelligence

### Moderately Assessable: Cognitive Bias Awareness

**Assessment Approach:**
- Present scenarios where cognitive biases might influence decisions
- Evaluate whether the model identifies potential biases and suggests debiasing strategies

**Assessment Criteria:**
- Does the model identify relevant cognitive biases?
- Does it suggest practical approaches to mitigate these biases?
- Does it demonstrate awareness of its own potential limitations?

**Sample Prompt:**
```
A team of experts is making predictions about a new technology's impact. What cognitive biases might affect their forecasts, and how could they mitigate these biases?
```

**Assessment Criteria for Response:**
- Identifies relevant biases (e.g., optimism bias, confirmation bias)
- Suggests specific debiasing techniques
- Discusses structural approaches to improve decision quality
- Acknowledges limitations of purely technical solutions to cognitive biases

### Moderately Assessable: Empathetic Reasoning

**Assessment Approach:**
- Evaluate the model's ability to reason from diverse perspectives
- Assess whether it demonstrates understanding of different lived experiences

**Sample Prompt:**
```
A city is implementing a new public transportation system. How might this change be experienced differently by various community members, including those with disabilities, the elderly, parents with young children, and low-income workers?
```

**Assessment Criteria:**
- Demonstrates understanding of diverse lived experiences
- Avoids stereotyping or oversimplification
- Identifies both practical and emotional aspects of different perspectives
- Suggests approaches that accommodate diverse needs

---

This framework provides a structured approach to evaluating wide-boundary intelligence in LLMs, focusing on the dimensions and sub-dimensions most amenable to assessment. The assessment criteria and sample prompts can be adapted or expanded based on specific evaluation needs.

</response 2>
