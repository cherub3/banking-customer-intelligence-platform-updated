# Resume Assets: Banking Customer Intelligence & Risk Analytics Pipeline

---

## Dashboard Screenshots Checklist

Take screenshots in this order. Each should be full-browser width, no browser chrome if possible. Use browser zoom at 80% for wider captures.

### 1. Executive Overview — Full Page
- URL: `http://localhost:8501` (defaults to Executive Overview)
- Capture: 5 KPI cards · 3 donuts · top-10 revenue bar · 4 P1 exception cards · 3 insight boxes
- Best for: GitHub README hero image, CV header graphic

### 2. Executive Overview — KPI Row Close-Up
- Crop the top row of 5 cards (Portfolio Revenue · Active Customers · Concentration Risk · P1 Alerts · Revenue at Risk)
- Shows the CRITICAL badge clearly
- Best for: LinkedIn post, portfolio site

### 3. Customer Intelligence — Health Heatmap
- Navigate to Customer Intelligence
- Capture the Segment × Health heatmap (left) + Revenue vs Health scatter (right)
- Best for: demonstrating SQL segmentation and visualisation skill

### 4. Customer Intelligence — Full Filtered Table
- Apply filter: Segment = VIP, Health = At-Risk + Watchlist
- Capture the filtered KPIs + customer detail table with health score progress bars
- Best for: showing interactivity and analyst-grade filtering

### 5. Risk & Exceptions — P1 Cards
- Navigate to Risk & Exceptions
- Capture the P1 alert banner + 4 P1 exception cards
- Shows the exception engine in action — this is the strongest story for a risk analyst role

### 6. RM Action Centre — Workbook
- Navigate to RM Action Centre
- Capture the 4 priority KPI cards + stacked action type bar + first 10 rows of the workbook
- Best for: demonstrating operational analytics and RM workflow thinking

### 7. Management Pack — Full Page
- Navigate to Management Pack
- Capture the navy report header + 6 KPI cards + all 4 key findings
- Best for: demonstrating executive communication, business storytelling, management reporting

### 8. Sidebar Navigation — Expanded
- Capture the left sidebar with Portfolio / Operations / Reports navigation groups visible
- Shows multi-page app architecture at a glance

---

## Resume Bullet Points

Use 3–5 of these depending on the target role. Lead with the metric; end with the business implication.

### Data Engineering / Analytics Engineering
- Built an end-to-end banking analytics pipeline on DuckDB — 9 incremental SQL layers transforming 152,502 transactions across 1,000 customers into a structured analytical schema, mirroring dbt-style modelling patterns used in production data teams
- Designed and implemented a 5-segment customer model (VIP / Growth / Regular / At-Risk / Dormant) using RFM scoring, enabling automated prioritisation of 1,000 RM-assigned actions by segment and revenue risk

### Risk / Business Analysis
- Built an automated exception detection engine identifying 652 open risks across 5 exception types (P1–P3 severity), surfacing a CRITICAL revenue concentration signal: 10 clients generating 51.4% of £1.71M portfolio income
- Detected 4 VIP clients with 22–29% quarterly revenue declines before standard health-category reporting would have flagged them — modelling the early-warning capability banks deploy in relationship monitoring systems

### Dashboard / Visualisation
- Developed a 5-page executive Streamlit dashboard (Plotly + DuckDB) styled to banking BI standards — portfolio KPIs, health matrix heatmap, RM action workbook, and a management pack formatted for board distribution
- Engineered a customer health scoring model across 4 dimensions (revenue trend, engagement, relationship breadth, portfolio momentum) producing a 0–100 composite score for 860 active banking customers

### General / Multi-Skill Bullet
- Delivered a full-stack banking analytics project — SQL data pipeline (DuckDB, 9 layers), customer segmentation, risk exception engine, and Streamlit executive dashboard — demonstrating the end-to-end workflow of a banking data analyst from raw transaction data to board-ready management pack

---

## Interview Talking Points

### "Tell me about a project you're proud of"

> "I built a full banking customer intelligence platform from scratch. It takes 152,502 transactions across 1,000 customers and runs them through a 9-layer SQL pipeline — starting with raw transaction staging, then RFM scoring, then a 5-segment customer model, and finally an exception detection engine that raises P1/P2/P3 alerts automatically. The output feeds a 5-page Streamlit dashboard styled to match what you'd see in a relationship banking BI tool.
>
> The most interesting finding was a revenue concentration issue I called CRITICAL: 10 clients generate 51.4% of all portfolio fee income, with a 13× revenue cliff between rank 10 and rank 11. The exception engine caught 4 VIP clients with 22–29% quarterly revenue declines — but their overall health scores were still Healthy. That's exactly the kind of early-warning signal that prevents churn from becoming a crisis."

---

### "How did you approach the customer segmentation?"

> "I used a deterministic RFM model — Recency, Frequency, Monetary value — scored on three 1–5 scales for each customer, then mapped the composite score to one of five segments: VIP, Growth, Regular, At-Risk, and Dormant.
>
> The key design decision was making it deterministic, not probabilistic. Banks need auditable, explainable models — you have to be able to tell a RM exactly why a client was moved from Growth to At-Risk. Probabilistic clustering doesn't give you that. A rule-based segment model with clear thresholds does.
>
> I then layered a 4-dimension health score on top of the segments: revenue trend, transaction engagement, product breadth, and portfolio momentum. This catches cases where a client is still in the VIP segment but their health trajectory is deteriorating — which is exactly the P1 exception scenario."

---

### "How did you build the exception engine?"

> "The exception engine is layer 7 in the pipeline, sitting on top of the health scores and segmentation. I defined 5 exception types, each with a SQL trigger condition and a severity mapping.
>
> The most important one is VIP Revenue Decline — triggered when a VIP client shows more than 20% QoQ revenue decline. That goes straight to P1 because the revenue concentration is so high that losing one of those clients has portfolio-level impact.
>
> The interesting engineering challenge was making sure exceptions fire on leading indicators, not lagging ones. If you wait until a client's health score falls to Critical, you've missed the intervention window. So the exception conditions look at direction of travel — is a Healthy client's revenue declining? That's the 24 accounts I flagged as Healthy-but-Deteriorating."

---

### "What would you change or extend if this were a real production system?"

> "Three things immediately. First, I'd replace the synthetic data generator with actual core banking system feeds — either direct DB replication or a Kafka event stream. The pipeline structure is already set up for this: the staging layer handles all cleansing, so swapping the source just means changing the ingestion method.
>
> Second, I'd add time-series tracking on the health scores. Right now the pipeline runs as a point-in-time snapshot. In production you'd want a daily scheduled run that writes each score to a history table, so you can show RM trend lines over 6–12 months and catch deterioration even earlier.
>
> Third, I'd add user authentication and RM-level data filtering to the dashboard so each RM only sees their own portfolio — that's standard for a client-facing BI tool in banking. The data structure already supports it because every record has an assigned_rm field."

---

### "What does the dashboard actually show?"

> "Five pages, each for a different audience. Executive Overview is for the CFO and portfolio risk committee — 5 KPI cards, three Plotly donuts for concentration/health/trend, a top-10 revenue bar chart, and the P1 exception cards.
>
> Customer Intelligence is for portfolio managers — it's a filterable explorer across all 1,000 customers with a health heatmap matrix and revenue-vs-health scatter.
>
> Risk & Exceptions is the alert feed for RM operations — P1 banner, exception breakdown chart, full filterable exception table.
>
> RM Action Centre is the day-to-day workbook — 1,000 prioritised actions, sorted P1 to P4, with instructions for each customer.
>
> Management Pack is designed to be screenshotted or printed — navy report header, all the key findings in a business-narrative format, and a priority action agenda table. It's the kind of one-pager you'd send to a risk committee before a quarterly review."

---

### "Why DuckDB instead of PostgreSQL or Snowflake?"

> "For a portfolio project demonstrating analytics skills, DuckDB was the right call for three reasons.
>
> First, zero infrastructure — the entire database is a single file. Anyone can clone the repo, run the build script, and have the full pipeline running in under two minutes. No database server, no credentials, no cloud account.
>
> Second, DuckDB's columnar execution is significantly faster than row-based engines for the aggregation patterns I'm using — GROUP BY, window functions, large scans across 152,502 rows. The SQL syntax is also compatible with BigQuery and Snowflake dialects, so the models transfer directly.
>
> Third, it's genuinely used in production analytics now — embedded in data science workflows, in dbt pipelines, in Python notebooks. It's not a toy."
