"""
The five ADK agents for root-cause analysis.
"""
from google.genai import client as genai_client
from google.adk import agent, parallel_agent, sequential_agent
from .tools import (
    get_metric_tree, get_distributor_info, 
    get_alert_details, get_historical_trend
)

MODEL = "gemini-2.0-flash-001"

# ============================================================================
# DISTRIBUTOR AGENT
# ============================================================================

distributor_agent = agent.LlmAgent(
    name="distributor_agent",
    model=MODEL,
    description="Investigates distributor count (D) and coverage (R/D)",
    instruction="""
You own TWO factors: distributor_count (D) and retailers_per_dist (R/D).

You will receive metric tree data for a town-division that has collapsed.
Use get_metric_tree to fetch the current state and get_historical_trend to see what changed.

Decision rules:
1. If D is 0 or dropped significantly: the distributor appointment failed or they exited.
2. If D is flat but R/D dropped: the distributor is shedding retailers.
3. If D and R/D are both stable: this is NOT your finding.

ALWAYS report whether this cell was sole-sourced (D=1) because if so, 
the collapse is TOTAL and has no redundancy.

Return JSON with:
- moved: true/false (did D or R/D move?)
- confidence: 0.0-1.0
- factor: "distributor_count" or "retailers_per_dist" or "both" or null
- explanation: brief summary
- sole_sourced: true/false
- named_entity: distributor_id if known, else null
""",
    tools=[get_metric_tree, get_distributor_info, get_alert_details, get_historical_trend],
    output_key="distributor_finding",
)

# ============================================================================
# ACTIVATION AGENT
# ============================================================================

activation_agent = agent.LlmAgent(
    name="activation_agent",
    model=MODEL,
    description="Investigates activation rate (a) — are retailers active?",
    instruction="""
You own ONE factor: active_rate (a).

active_rate is the fraction of mapped retailers who placed at least one order.
If it drops, retailers stopped ordering—a signal of demand destruction or switching.

Use get_metric_tree to see current a and get_historical_trend to see the baseline.

Decision rules:
1. If a dropped >20% from baseline: demand is collapsing at the retailer level.
2. If a is flat: this is NOT your finding. Defer to other agents.
3. If a is rising while sales fell: frequency or value must be down.

Return JSON with:
- moved: true/false
- confidence: 0.0-1.0
- pct_change: percentage change from baseline
- explanation: brief summary
""",
    tools=[get_metric_tree, get_historical_trend],
    output_key="activation_finding",
)

# ============================================================================
# FREQUENCY AGENT
# ============================================================================

frequency_agent = agent.LlmAgent(
    name="frequency_agent",
    model=MODEL,
    description="Investigates order frequency (f) — are orders less frequent?",
    instruction="""
You own ONE factor: frequency (f) — orders per active retailer per month.

If frequency drops, active retailers are ordering less often.
This often signals inventory sufficiency or slowdown in the channel.

Use get_metric_tree to see current f and get_historical_trend to see the baseline.

Decision rules:
1. If f dropped >15% from baseline: retailers are ordering less. Investigate supply chain delays.
2. If f is flat: this is NOT your finding.
3. If f is rising while sales fell: value must be down significantly.

Return JSON with:
- moved: true/false
- confidence: 0.0-1.0
- pct_change: percentage change from baseline
- explanation: brief summary
""",
    tools=[get_metric_tree, get_historical_trend],
    output_key="frequency_finding",
)

# ============================================================================
# VALUE AGENT
# ============================================================================

value_agent = agent.LlmAgent(
    name="value_agent",
    model=MODEL,
    description="Investigates average order value (v) — are orders smaller?",
    instruction="""
You own ONE factor: avg_value (v) — average revenue per order.

If value drops, orders are smaller (lower price point products, discounts, or mix shift).

Use get_metric_tree to see current v and get_historical_trend to see the baseline.

Decision rules:
1. If v dropped >15% from baseline: orders are smaller. Mix shift to lower-margin products?
2. If v is flat: this is NOT your finding.
3. If v is rising while sales fell: activation or frequency must be down significantly.

Return JSON with:
- moved: true/false
- confidence: 0.0-1.0
- pct_change: percentage change from baseline
- explanation: brief summary
""",
    tools=[get_metric_tree, get_historical_trend],
    output_key="value_finding",
)

# ============================================================================
# PIPELINE AGENT
# ============================================================================

pipeline_agent = agent.LlmAgent(
    name="pipeline_agent",
    model=MODEL,
    description="Investigates supply-demand balance",
    instruction="""
You do NOT own a specific factor. You investigate STRUCTURAL mismatches:
- Is the distributor's stock adequate for demand?
- Did supply chain delays disrupt fulfillment?
- Is there a price/promotion mismatch?

Use get_distributor_info to see channel structure and get_historical_trend for context.

Return JSON with:
- moved: true/false
- confidence: 0.0-1.0
- issue: "supply_constrained" or "demand_destroyed" or "price_mismatch" or null
- explanation: brief summary
""",
    tools=[get_distributor_info, get_historical_trend, get_alert_details],
    output_key="pipeline_finding",
)