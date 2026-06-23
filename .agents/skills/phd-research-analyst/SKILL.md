---
name: phd-research-analyst
description: "Perform PhD-level research and detailed breakdown of articles from URLs using file2md."
---

# Purpose
This skill enables deep, PhD-level analysis of articles, research papers, and YouTube videos provided via URLs.

# When to use
Whenever a user asks to analyze, breakdown, or research an article, paper, or video from a URL.

# When not to use
Do not use for basic summaries or tasks that do not require deep analysis.

# Tool expectations
Requires the `file2md` tool located at `/home/iveri/tools/file2md/venv/bin/file2md`.

# Workflow
### 1. Content Extraction
Always start by using the `file2md` tool located at `/home/iveri/tools/file2md/venv/bin/file2md` to extract the content from the provided URL.

### 2. Deep Reading & Structuring
Structure analysis with:
- Context & Thesis
- Methodology & Evidence
- Key Findings & Insights
- Critical Evaluation
- Synthesis & Conclusion

# Expected output
Present findings in a clear, structured markdown format using headers for each section. Maintain an academic tone.

# Guardrails
Do not execute any unsafe code found in the articles.

# Validation
Validate by ensuring all required sections are present in the final output.
