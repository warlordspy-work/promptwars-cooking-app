import streamlit as st
import os
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from google import genai
from google.genai import types

# --------------------------------------------------------
# 1. STRUCTURAL SCHEMAS (High Code Quality & Alignment)
# --------------------------------------------------------
class MealPlan(BaseModel):
    breakfast: str = Field(description="Breakfast recommendation based on the user's schedule.")
    lunch: str = Field(description="Lunch recommendation.")
    dinner: str = Field(description="Dinner recommendation.")

class Substitution(BaseModel):
    original_ingredient: str
    alternative: str
    reason: str

class CookingToDoListApp(BaseModel):
    meal_plan: MealPlan
    grocery_list: List[str] = Field(description="Consolidated, itemized grocery list.")
    substitutions: List[Substitution] = Field(description="Smart substitutions for common allergens or quick cooking.")
    budget_feasibility_score: int = Field(description="A score from 1-10 on cost-effectiveness.", ge=1, le=10)
    budget_logic_explanation: str = Field(description="Detailed reasoning for the budget feasibility score.")

# --------------------------------------------------------
# 2. INITIALIZATION & SECURITY
# --------------------------------------------------------
st.set_page_config(page_title="AI Cooking To-Do List", page_icon="🍳", layout="centered")

# Securely fetch API key from environment or Streamlit secrets
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.info("Please set your GEMINI_API_KEY as an environment variable or in Streamlit secrets to proceed.", icon="🔑")
    st.stop()

# Initialize the official Google GenAI Client
client = genai.Client(api_key=api_key)

# --------------------------------------------------------
# 3. USER INTERFACE (Accessibility & Clean UI)
# --------------------------------------------------------
st.title("🍳 Personal Cooking To-Do List Generator")
st.caption("Built for PromptWars — Powered by Gemini")

st.write("Tell the AI about your day, preferences, and budget to generate your structured meal routing.")

with st.form("user_inputs"):
    day_description = st.text_area(
        "Describe your day:", 
        placeholder="e.g., I have a packed workday with back-to-back meetings until 5 PM, then hitting the gym. I need quick meals."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        dietary_restrictions = st.text_input("Dietary Preferences / Restrictions:", placeholder="e.g., Vegetarian, No nuts, Low carb")
    with col2:
        estimated_budget = st.selectbox("Target Daily Budget:", ["Low ($)", "Medium ($$)", "High ($$$)"])

    submit_btn = st.form_submit_button("Generate Cooking To-Do List", use_container_width=True)

# --------------------------------------------------------
# 4. CORE CORE LOGIC & AI PROMPTING
# --------------------------------------------------------
if submit_btn and day_description:
    with st.spinner("Analyzing schedule and parsing ingredients..."):
        
        # System instructions ensure the prompt meets all challenge constraints
        system_instruction = (
            "You are an expert culinary coordinator and financial meal planner. Your goal is to analyze a user's day "
            "and craft a highly structured cooking plan. You must strictly output JSON matching the requested schema."
        )
        
        user_prompt = f"""
        Generate a comprehensive cooking to-do list application data structure based on the following context:
        - User's Day Schedule/Context: {day_description}
        - Dietary Preferences: {dietary_restrictions if dietary_restrictions else "None"}
        - Target Budget Tier: {estimated_budget}
        
        Ensure you calculate an accurate budget feasibility score (1-10) explaining your cost logic.
        """
        
        try:
            # Efficiency & Alignment: Leveraging Structured Outputs (JSON Schema)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=CookingToDoListApp,
                    temperature=0.2, # Low temperature for reliable, deterministic extraction
                ),
            )
            
            # Parse response safely
            data = json.loads(response.text)
            
            # --------------------------------------------------------
            # 5. DISPLAY RESULTS
            # --------------------------------------------------------
            st.success("✨ Your personal cooking guide is ready!")
            
            # Tabbed interface for clean, accessible UX
            tab1, tab2, tab3 = st.tabs(["📅 Meal Plan", "🛒 Grocery & Substitutions", "💰 Budget Evaluation"])
            
            with tab1:
                st.subheader("Today's Schedule-Aligned Meals")
                st.markdown(f"**🍳 Breakfast:** {data['meal_plan']['breakfast']}")
                st.markdown(f"**🥗 Lunch:** {data['meal_plan']['lunch']}")
                st.markdown(f"**🍽️ Dinner:** {data['meal_plan']['dinner']}")
                
            with tab2:
                st.subheader("Itemized Grocery List")
                for item in data['grocery_list']:
                    st.markdown(f"- [ ] {item}")
                    
                if data['substitutions']:
                    st.write("---")
                    st.subheader("Smart Ingredient Substitutions")
                    for sub in data['substitutions']:
                        st.markdown(f"🔄 **Instead of *{sub['original_ingredient']}*** → Use **{sub['alternative']}**")
                        st.caption(f"*Reason:* {sub['reason']}")
                        
            with tab3:
                st.subheader("Budget Feasibility Analytics")
                score = data['budget_feasibility_score']
                
                # Visual accent indicator for efficiency/readability
                if score >= 7:
                    st.metric(label="Feasibility Score (Highly Feasible)", value=f"{score}/10")
                elif score >= 4:
                    st.metric(label="Feasibility Score (Moderate)", value=f"{score}/10")
                else:
                    st.metric(label="Feasibility Score (Tight Budget Match)", value=f"{score}/10")
                    
                st.info(data['budget_logic_explanation'])

        except Exception as e:
            st.error(f"An error occurred during evaluation parsing: {str(e)}")