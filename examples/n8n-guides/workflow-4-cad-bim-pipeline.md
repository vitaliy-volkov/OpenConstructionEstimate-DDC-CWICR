# Workflow 4: CAD/BIM Cost Estimation Pipeline (4D/5D)

**File:** `2_n8n_Pipelines_Cost_Calculation/n8n_4_CAD_(BIM)_Cost_Estimation_Pipeline_4D_5D_with_DDC_CWICR.json`
**Workflow name:** V3.1 CAD (BIM) Cost Estimation Pipeline with DDC CWICR

An automated 10-stage pipeline that takes a Revit/BIM model file and produces a complete cost estimate with phase scheduling (4D) and cost breakdown (5D) using the DDC CWICR database.

---

## What It Does

1. Extracts quantity takeoff data from a Revit model (via the DDC Converter)
2. Classifies building elements vs. non-physical elements using AI
3. Generates construction phases and assigns elements to phases
4. Decomposes each element into granular construction work items
5. Searches the DDC CWICR database for matching unit costs
6. Calculates total costs and aggregates by phase
7. Produces formatted reports (HTML, Excel, PDF)

---

## Prerequisites

- n8n instance (self-hosted)
- OpenAI API key
- Qdrant with DDC CWICR collections loaded
- **DDC Converter (RvtExporter.exe)** -- Revit-to-Excel export tool
- Revit model file (.rvt, supports Revit 2015-2026)

---

## Required Credentials

Configure in the `Setup - Define file paths` node:

| Field | Value | Description |
|-------|-------|-------------|
| `path_to_converter` | Path to `RvtExporter.exe` | DDC Converter executable |
| `project_file` | Path to `.rvt` file | Revit model to estimate |
| `group_by` | `"Type Name"` | How to group elements |
| `language_code` | `"DE"`, `"EN"`, etc. | Target language/region |
| `user_project_description` | Free text | Optional project context |

OpenAI credentials are configured via n8n's built-in credential system.

---

## The 10-Stage Pipeline

### Stage 0: Collect BIM Data

Runs the DDC Converter (`RvtExporter.exe`) against the Revit file to extract element data as an Excel spreadsheet. The converter exports all model elements with their properties: category, type name, dimensions, volumes, areas, and material information.

Elements not visible in 3D views are separated and excluded from cost estimation.

### Stage 1: Detect Project Type

AI analyzes the extracted element data to determine the project type:
- Residential / Commercial / Industrial / Infrastructure
- New construction / Renovation / Mixed

This classification influences how work items are decomposed in later stages.

### Stage 2: Generate Construction Phases

AI generates a logical sequence of construction phases based on the project type and element categories. For example:
- Phase 1: Site Preparation & Earthworks
- Phase 2: Foundation
- Phase 3: Structural Frame
- Phase 4: Building Envelope
- Phase 5: Interior Finishing
- Phase 6: MEP Systems

### Stage 3: Assign Elements to Phases

Each element group from the BIM model is assigned to the appropriate construction phase. AI maps element categories (walls, floors, roofs, MEP) to the generated phases.

### Stage 4: Decompose to Work Items

The core estimation stage. For each building element, AI decomposes it into granular construction work items with quantities. For example, a "Concrete Wall" element becomes:
- Formwork installation (area)
- Rebar placement (weight)
- Concrete pouring (volume)
- Formwork removal (area)
- Surface finishing (area)

### Stage 5: Vector Search Pricing

Each decomposed work item is embedded using OpenAI `text-embedding-3-large` and searched against the appropriate DDC CWICR Qdrant collection. Returns the closest matching work items with unit costs.

### Stage 6: Map Units

Aligns the units from the BIM model (which may vary) with the units in the DDC CWICR database. Handles conversions between metric units (m, m2, m3, kg, t) and resolves unit mismatches.

### Stage 7: Calculate Costs

Multiplies matched unit costs by quantities from the BIM model. Produces per-item costs and running totals. Applies any regional cost adjustments.

### Stage 7.5: Validate Works

Quality check stage. AI reviews the calculated costs for anomalies:
- Unusually high or low unit costs
- Missing work items for element types
- Quantity sanity checks against BIM geometry

### Stage 8: Aggregate by Phases

Rolls up individual work item costs into phase totals. Produces a phase-by-phase cost summary with subtotals and a grand total.

### Stage 9: Generate Reports

Formats the final output:
- **HTML report** -- interactive cost breakdown with phase structure
- **Excel export** -- detailed spreadsheet with all work items
- **PDF report** -- formatted document for stakeholders

---

## Node Flow (Simplified)

```
Manual Trigger
  --> Setup (file paths, language)
  --> Configure Language & Vector DB
  --> DDC Converter (Revit --> Excel)
  --> Read & Parse Excel
  --> Extract Headers and Data
  |
  --> Find Category Fields
  --> AI Classify Categories (building vs. drawing elements)
  --> Apply Classification to Groups
  --> Filter: Building Elements Only
  |
  --> AI Aggregation Rules (determine sum/mean/first/last per field)
  --> Group Data with AI Rules
  |
  --> [Loop over element groups]
  |     --> AI Detect Project Type (Stage 1)
  |     --> AI Generate Phases (Stage 2)
  |     --> AI Assign to Phases (Stage 3)
  |     --> AI Decompose to Works (Stage 4)
  |     --> Embed Work Descriptions
  |     --> Qdrant Vector Search (Stage 5)
  |     --> Map Units (Stage 6)
  |     --> Calculate Costs (Stage 7)
  |     --> Validate (Stage 7.5)
  |
  --> Aggregate by Phases (Stage 8)
  --> Generate Reports (Stage 9)
```

---

## Language & Region Configuration

The `Configure Language & Vector DB` node maps language codes to regional settings:

| Code | Language | City | Collection | Currency |
|------|----------|------|-----------|----------|
| DE | German | Berlin | Qdrant DE collection | EUR |
| EN | English | Toronto | Qdrant EN collection | CAD $ |
| FR | French | Paris | Qdrant FR collection | EUR |
| ES | Spanish | Barcelona | Qdrant ES collection | EUR |
| RU | Russian | St. Petersburg | Qdrant RU collection | RUB |
| PT | Portuguese | Sao Paulo | Qdrant PT collection | BRL |
| ZH | Chinese | Shanghai | Qdrant ZH collection | CNY |
| AR | Arabic | Dubai | Qdrant AR collection | AED |
| HI | Hindi | Mumbai | Qdrant HI collection | INR |

---

## Element Classification

The pipeline uses a two-pass classification system:

1. **Hard Exclude** -- pattern-based filtering of non-physical elements:
   - Levels, Grids, Reference Planes, Scope Boxes
   - Annotations, Dimensions, Text Notes, Tags
   - Views, Sheets, Schedules, Legends
   - RPC objects (entourage people, cars)

2. **AI Classification** -- LLM-based classification of remaining elements into building vs. drawing categories, with confidence scores.

---

## Customization

### Changing the Target Language
In the `Setup - Define file paths` node, change `language_code` to any supported code (DE, EN, FR, ES, RU, PT, ZH, AR, HI).

### Limiting Element Groups
For testing, the workflow includes an optional "Only 10 Groups" limiter node. Disable it for full model processing.

### Adjusting AI Prompts
Each AI stage has specialized prompts. Key prompts to customize:
- **Stage 1** prompt controls project type detection
- **Stage 4** prompt controls work item decomposition granularity
- **Stage 7.5** prompt controls validation sensitivity

### Supporting Non-Revit Models
The pipeline can work with any BIM tool that exports to Excel with element categories and quantities. Replace the DDC Converter stage with your own export mechanism.

---

## Testing

1. Import the workflow JSON into n8n
2. Set file paths in the Setup node:
   - Path to `RvtExporter.exe`
   - Path to a `.rvt` test file
3. Set `language_code` (e.g., `"DE"` for German)
4. Configure OpenAI credentials in n8n
5. Click "Execute workflow" (manual trigger)
6. Monitor execution through all 10 stages
7. Verify the final report output

For faster iteration, enable the "Only 10 Groups" limiter to process a subset of elements.
