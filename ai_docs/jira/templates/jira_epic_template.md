# Jira Epic Template — Reference

Use this template to author Epics. Copy the sections into the Epic description and fill them out. Keeping Epics consistent improves planning, prioritization, and stakeholder communication.

#Summary
-----
Concise, clear, ≤ 100 characters; identifies outcome and domain. 
  - Example: “Data Services – Revenue Leakage – Automated Detection of Misclassification in Image RPS and CTI Billing”

##Description
-----------
Narrative explains context, problem/opportunity, and outcome; includes “Description” section.
  - Example: Paragraphs define who, what, why

  **Business Value**
    - Quantified drivers (cost, CSAT/NPS, efficiency, scalability) with $ impact
    - Example: "Reduces revenue leakage by $1.5M annually; improves CSAT by 10 pts"

  **Scope (in/out)**
    - Clear boundaries; explicit out-of-scope items listed
    - Example: "In-scope: RPS billing; Out-of-scope: native mobile apps"

  **Acceptance Criteria**
    - Specific, testable, measurable criteria that define “done” at epic level
    - Example: "System detects misclassification with ≥95% accuracy; alerts logged within 5 mins"

  **User Stories**
    - Stories cover all included scope areas; traceable to acceptance criteria
    - Example: "Story IDs mapped to Epic ID; each story addresses a scope item"

  **Dependencies**
    - Internal/external/technical dependencies with owners and dates
    - Example: "Depends on image model API (owner: Data Eng, date: 03/15)"

  **Risk & Mitigations**
    - High/Medium risks with impact, mitigation, owner, timeline; weekly monitoring plan
    - Example: "Risk: Model drift; Mitigation: retrain quarterly (owner: AI team)"

  **Additional Notes**
    - Named team(s) with purpose + roster; single accountable owner; extra context
    - Example: "Teams: AI4Biz, AI4Tech; Owner: Product Manager; Context: aligns with automation roadmap"
