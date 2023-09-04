#!/usr/bin/env python
# coding: utf-8

# ## Csv Analysis

# In[2]:


import pandas as pd


# In[3]:


# pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


# In[22]:


import pandas as pd

def sort_funding_sources():
    df = pd.read_csv("funding_sources.csv")
    # Sort the DataFrame using 'fiscalYear' as the primary column and 'fundingAmount' as the secondary column
    df_sorted = df.sort_values(by=['fiscalYear', 'fundingAmount'], ascending=[False, False])
    return df_sorted

def merge_and_sort(projects_func, funding_func):
    # Call the provided functions to get the sorted DataFrames
    sorted_funding_sources_df = funding_func()

    # Filter the projects DataFrame to keep only rows with 'Future' in 'projectStatus' column
    projects_df = projects_func()
    future_projects_df = projects_df[projects_df['projectStatus'].str.contains('Future', case=False) & projects_df['projectStatus'].notna()]

    # Merge the DataFrames based on 'parentUII' and 'currenttUII' columns
    merged_df = pd.merge(sorted_funding_sources_df, future_projects_df, left_on='parentUII', right_on='currentUII')

    # Sort the merged DataFrame based on 'fiscalYear' and 'fundingAmount'
    merged_sorted_df = merged_df.sort_values(by=['fiscalYear', 'fundingAmount'], ascending=[False, False])

    return merged_sorted_df

# Call the merge_and_sort function to get the final merged and sorted DataFrame
final_merged_sorted_df = merge_and_sort(sort_projects, sort_funding_sources)

# Print the final merged and sorted DataFrame
(final_merged_sorted_df)


# In[23]:


final_merged_sorted_df_50=final_merged_sorted_df.head(50)


# In[24]:


final_merged_sorted_df_50


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




