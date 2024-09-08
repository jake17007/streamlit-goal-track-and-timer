import streamlit as st
import datetime
import time
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session state variables
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'update_status' not in st.session_state:
    st.session_state.update_status = {}

def create_goal(name, duration):
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=duration)
    return {
        'name': name,
        'start_time': start_time,
        'end_time': end_time,
        'status': 'Active'
    }

def update_goal_status(goal_index, new_status):
    goal = st.session_state.goals[goal_index]
    goal['status'] = new_status
    if new_status == 'Completed':
        st.success(f"Goal '{goal['name']}' marked as completed!")
    elif new_status == 'Abandoned':
        st.warning(f"Goal '{goal['name']}' marked as abandoned.")
    elif new_status == 'Deleted':
        st.session_state.goals.pop(goal_index)
        st.info(f"Goal '{goal['name']}' has been deleted.")
    st.session_state.update_status[goal_index] = False

def format_time(dt):
    return dt.strftime("%I:%M %p")  # 12-hour time with AM/PM

def format_timedelta(td):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def interpret_input(input_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that interprets goal descriptions and extracts the goal name and duration in minutes. Respond with a JSON object containing 'goal_name' and 'duration_minutes'."},
            {"role": "user", "content": f"Interpret this goal: {input_text}"}
        ]
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        return result['goal_name'], result['duration_minutes']
    except (json.JSONDecodeError, KeyError):
        return None, None

st.title("Goal Tracker & Timer")

# Goal Creation Section
st.header("Create a New Goal")
goal_input = st.text_input("Enter your goal and duration (e.g., 'get code to work within 1 hour and 30 min')")

if st.button("Add Goal"):
    if goal_input:
        goal_name, duration_minutes = interpret_input(goal_input)
        
        if goal_name and duration_minutes:
            new_goal = create_goal(goal_name, duration_minutes)
            st.session_state.goals.append(new_goal)
            st.success(f"Goal '{goal_name}' added successfully for {duration_minutes} minutes!")
        else:
            st.error("Couldn't interpret the input. Please try again with a clear goal and duration.")
    else:
        st.error("Please enter a goal and duration.")

# Active Goals Section
st.header("Active Goals")
for idx, goal in enumerate(st.session_state.goals):
    if goal['status'] == 'Active':
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{goal['name']}**")
        with col2:
            st.write(f"Start: {format_time(goal['start_time'])}")
        with col3:
            st.write(f"End: {format_time(goal['end_time'])}")
        with col4:
            remaining_time = goal['end_time'] - datetime.datetime.now()
            if remaining_time.total_seconds() > 0:
                st.write(f"Left: {format_timedelta(remaining_time)}")
            else:
                st.write("Time's up!")
        
        # Initialize update_status for this goal if not exists
        if idx not in st.session_state.update_status:
            st.session_state.update_status[idx] = False

        if st.button("Update Status", key=f"update_button_{idx}"):
            st.session_state.update_status[idx] = True

        if st.session_state.update_status[idx]:
            new_status = st.selectbox(
                "Select new status",
                ["Active", "Completed", "Abandoned", "Deleted"],
                key=f"status_{idx}"
            )
            if st.button("Confirm Status Update", key=f"confirm_{idx}"):
                update_goal_status(idx, new_status)

# Goal History Section
st.header("Goal History")
completed_goals = [goal for goal in st.session_state.goals if goal['status'] == 'Completed']
abandoned_goals = [goal for goal in st.session_state.goals if goal['status'] == 'Abandoned']

st.subheader("Completed Goals")
for goal in completed_goals:
    st.write(f"- {goal['name']} (Completed at: {format_time(goal['end_time'])})")

st.subheader("Abandoned Goals")
for goal in abandoned_goals:
    st.write(f"- {goal['name']} (Abandoned at: {format_time(goal['end_time'])})")

# Refresh button to manually update the app
if st.button('Refresh'):
    st.rerun()

# Auto-refresh using Streamlit's auto-rerun feature
time.sleep(1)
st.rerun()