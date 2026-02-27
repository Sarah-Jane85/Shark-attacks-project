## SharkSafe: Enhancing Diver Safety and Experiences Through Predictive Mapping of Shark Encounters

Overview
The SharkSafe project empowers divers by providing detailed insights into shark encounters. Our goal is to enhance both safety and the quality of the diving experience through data-driven predictive mapping. We analyze shark encounter data to educate divers on optimal locations and times for diving, minimizing risks and maximizing enjoyment.

Project Scope
Primary Hypothesis: Shark attacks are more likely to occur around midday, aligning with peak human activity, thus informing crucial safety advisories for divers.
Secondary Hypothesis: Contrary to initial assumptions, visibility conditions in January are decreased due to extreme weather events, leading to higher risks despite increased shark encounters.

---

## Data
This project utilizes shark encounter data that includes:

Date and Time
Location and Geographical Data
Details on Shark Species
Environmental Factors and Human Activity

## Difference Between DataClean and Seasonality Analysis

The project produces two main output datasets:

- **shark_attacks_clean.csv** (DataClean)
- **seasonality_analysis.csv** (Seasonality Analysis)

These files contain different levels of data detail.

---

## 1. DataClean Dataset (`shark_attacks_clean.csv`)

### Description

This is the **fully cleaned dataset**, where **each row represents a single shark attack**.

It is the direct output of the cleaning pipeline:



### Structure Example

| Case_Number_final | Country | Month_name | Time_category | Fatal Y/N | Year_final |
|------------------|---------|------------|--------------|-----------|-----------|

### Characteristics

- Row-level data (granular)
- Contains all cleaned variables
- One row = one attack

### Typical Uses

- Exploratory Data Analysis
- Statistical analysis
- Machine Learning
- Custom visualizations

### Example

| Country | Month_name | Time_category | Fatal Y/N |
|--------|-------------|--------------|----------|
| USA | July | Afternoon | Non-Fatal |
| USA | July | Afternoon | Fatal |
| Australia | January | Morning | Non-Fatal |

Each row represents **one individual shark attack**.

---

## 2. Seasonality Analysis Dataset (`seasonality_analysis.csv`)


Each row represents **a group of shark attacks**.

### Structure Example

| Country | Month_name | Time_category | Fatal Y/N | Attack_Count |
|--------|-------------|--------------|----------|-------------|

### Characteristics

- Aggregated data
- Groups multiple attacks together
- Includes attack counts

Column: Attack Count


represents the number of attacks in each group.

### Example

| Country | Month_name | Time_category | Fatal Y/N | Attack_Count |
|--------|-------------|--------------|----------|-------------|
| USA | July | Afternoon | Non-Fatal | 134 |
| USA | July | Afternoon | Fatal | 12 |

This means:

There were **134 non-fatal attacks** in the USA in July during the afternoon.

---

## Main Differences

| Feature | DataClean | Seasonality Analysis |
|---------|----------|-----------------------|
| Data Type | Detailed | Aggregated |
| Level | Individual attack | Group of attacks |
| Rows | Many (e.g. 25,000+) | Fewer |
| Attack_Count column | No | Yes |
| Primary Use | General analysis | Seasonality analysis |

---

## Conceptual Difference

## When to Use Each Dataset

### Use DataClean When

- Detailed analysis is required
- Creating new visualizations
- Filtering records
- Exploring the dataset

---

### Use Seasonality Analysis When

- Performing seasonal analysis
- Creating pivot tables
- Running fast aggregations
- Studying patterns by month or time of day

---

## Summary

**DataClean = individual attack records**

**Seasonality Analysis = aggregated attack counts**

The cleaned dataset (`shark_attacks_clean.csv`) contains individual attack records, while the seasonality dataset (`seasonality_analysis.csv`) contains aggregated counts used for seasonal analysis.

---

## Research Findings
Environmental Impact: Increased extreme weather events degrade visibility and heighten safety risks,
Human Activity Correlation: Higher attack rates align with midday human activity peaks.

---

## Contact
For questions or further collaboration, contact us at: info@sharksafe.com


