import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

import streamlit as st 
import sqlite3
import ast
import regex as re

# Enable wide layout
st.set_page_config(layout="wide")  

# Connect to sqlite database
conn    = sqlite3.connect('adzuna_jobs.db')

# Query jobs table from the database
jobs_df = pd.read_sql_query('select * from jobs', conn)

# Close the databse connection
conn.close()

# -------------------- Feature engineering -------------------- 
# Creating an area feature to reduce the number of locations
jobs_df['area'] = jobs_df['area_list'].apply(lambda x : ast.literal_eval(x)[1] if x else None)

# Creating a roles feature to reduce the number of titles
def classify_role(title):
    title = title.lower()

    if re.search(r'\bdata\b', title) and re.search(r'\b(science|scientist)\b', title):
        return 'Data Scientist'
    elif re.search(r'\bdata\b', title) and re.search(r'\b(analyst|analysis)\b', title):
        return 'Data Analyst'
    elif re.search(r'\bdata\b', title) and re.search(r'\b(engineering|engineer)\b', title):
        return 'Data Engineer'        
    elif re.search(r'\b(machine|ml|ai)\b', title) and re.search(r'\b(engineering|engineer|learning)\b', title):
        return 'ML Engineer'
    elif re.search(r'(actuarial|actuary)', title):
        return 'Actuarial Analyst'
    else:
        return 'Other'


jobs_df['role'] = jobs_df['title'].apply(classify_role)

# Creating an avg_salary feature
jobs_df['salary_avg'] = (jobs_df['salary_min'] + jobs_df['salary_max'])/2

# -------------------- Visualizations -------------------- 
# Title
st.title("Job Analysis Heatmaps")

# -------------------- Role vs category heatmap -------------------- 
# Creating roles and categories pivot table
pivot_1 = jobs_df.pivot_table(index='role', columns='category', values='id', aggfunc='count')

fig1 = px.imshow(pivot_1.values,
                labels=dict(x="Category", y="Role", color="Count"),
                x=pivot_1.columns,
                y=pivot_1.index,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                width=1000,
                height=600)

# -------------------- Role salaries across categories heatmap -------------------- 
pivot_2 = jobs_df.pivot_table(index='role', columns='category', values='salary_avg', aggfunc='mean')

fig2 = px.imshow(pivot_2.values,
            labels=dict(x="Category", y="Role", color="Mean"),
            x=pivot_2.columns,
            y=pivot_2.index,
            text_auto=True,
            color_continuous_scale='RdBu_r',
            width=1000,
            height=600)

# -------------------- Area vs role heatmap -------------------- 
pivot_3 = jobs_df.pivot_table(index='area', columns='role', values='id', aggfunc='count', fill_value=0)

fig3 = px.imshow(pivot_3.values,
                labels=dict(x="Role", y="Area", color="Count"),
                x=pivot_3.columns,
                y=pivot_3.index,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                width=700,
                height=550)

# -------------------- Area vs category heatmap -------------------- 
pivot_4 = jobs_df.pivot_table(index='area', columns='category', values='id', aggfunc='count', fill_value=0)

fig4 = px.imshow(pivot_4.values,
                labels=dict(x="Category", y="Area", color="Count"),
                x=pivot_4.columns,
                y=pivot_4.index,
                text_auto=True,
                color_continuous_scale='RdBu_r',
                width=1000,
                height=600)

# -------------------- Creating tabs on streamlit --------------------
tab1, tab2, tab3, tab4 = st.tabs(["Roles vs Category", "Role Salaries Across Categories", "Role Distribution Across Areas", "Category Distribution Across Areas"])

with tab1:
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.plotly_chart(fig4, use_container_width=True)    