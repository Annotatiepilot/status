# Databricks notebook source
# MAGIC %pip install --quiet --upgrade labelbox pytz

# COMMAND ----------

import os
import labelbox
LABELBOX_API_KEY = os.environ.get('LABELBOX_API_KEY') or dbutils.secrets.get('labelbox', 'API_KEY')
client = labelbox.Client(LABELBOX_API_KEY)

# COMMAND ----------

projects = {project.uid: project for project in client.get_projects()}

# COMMAND ----------

performance = {project.uid: list(project.labeler_performance()) for project in projects.values()}

# COMMAND ----------

import pandas
performance_df = []
for project_uid, performances in performance.items():
    performance_df.append(pandas.DataFrame(performances))
    performance_df[-1]['project_uid'] = project_uid
    performance_df[-1]['project_name'] = projects[project_uid].name
performance_df = pandas.concat(performance_df)
    
anonymize = lambda x: x.email[15].capitalize() + '*' * (len(x.email) - 15 - 12) + x.email[-11]
performance_df['user'] = performance_df.user.apply(anonymize)

# COMMAND ----------

project_df = performance_df.groupby('project_name').aggregate({'count': 'sum', 'total_time_labeling': 'sum'})
project_df['time_per_label'] = project_df['total_time_labeling'] / project_df['count']
project_df['fraction_time_labeling'] = project_df['total_time_labeling'] / project_df['total_time_labeling'].sum()
project_df

# COMMAND ----------

import matplotlib
import matplotlib.cm 
import matplotlib.pyplot
from datetime import datetime
import pytz

color_mapping = dict(zip(sorted(project_df.index), matplotlib.cm.tab10(range(len(project_df)))))

ax = project_df.sort_values('count')['count'].plot(kind='barh', color=[color_mapping[x] for x in project_df.index], figsize=(8, 3))
ax.set_ylabel('')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)

for p in ax.patches:
    p.set_height(0.7)
    p.set_y(p.get_y() - 0.1)
    ax.annotate(str(p.get_width()), (p.get_x() + p.get_width(), p.get_y() + p.get_height()/2), xytext=(-2, 0), ha='right', va='center', textcoords='offset points', color='w')
    
ax.set_title('Aantal geannotateerde items')
ax.set_xlabel('Laatst bijgewerkt: ' + datetime.now(pytz.timezone('Europe/Amsterdam')).strftime('%d-%m-%y %H:%M'))

root = '/dbfs/FileStore/dodijk/' if 'dbutils' in globals() else ''
matplotlib.pyplot.savefig(root + 'status.svg', bbox_inches='tight')