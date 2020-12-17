import streamlit as st
import time, json
import numpy as np
import altair as alt
import pandas as pd
import Robogame as rg
from scipy.stats import pearsonr
import seaborn as sns
import matplotlib.pyplot as plt


# let's create two "spots" in the streamlit view for our charts
status = st.empty()
time_show=st.empty()
parts_record=st.empty()
predVis = st.empty()
partVis = st.empty()

corr_text=st.empty()
corrVis1 = st.empty()
corrVis = st.empty()


# create the game, and mark it as ready
game = rg.Robogame("bob")
game.setReady()


# wait for both players to be ready
while(True):	
	gametime = game.getGameTime()
	timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
	
	if ('Error' in gametime):
		status.write("Error"+str(gametime))
		break
	if (timetogo <= 0):
		status.write("Let's go!")
		break
	status.write("waiting to launch... game will start in " + str(int(timetogo)))
	time.sleep(1) # sleep 1 second at a time, wait for the game to start

choose_part= None
# run 100 times
for i in np.arange(0,101):
	# sleep 6 seconds
	for t in np.arange(0,6):
		status.write("Seconds to next hack: " + str(6-t))
		time.sleep(1)

	# update the hints
	hints=game.getHints()

	# create a dataframe for the time prediction hints
	df1 = pd.DataFrame(game.getAllPredictionHints())

	# if it's not empty, let's get going
	if (len(df1) > 0):
		# create a plot for the time predictions (ignore which robot it came from)
		c1 = alt.Chart(df1).mark_circle().encode(
			alt.X('time:Q',scale=alt.Scale(domain=(0, 100))),
			alt.Y('value:Q',scale=alt.Scale(domain=(0, 100)))
		)

		# write it to the screen
		predVis.write(c1)

	# get the parts
	df2 = pd.DataFrame(game.getAllPartHints())

	# we'll want only the quantitative parts for this
	# the nominal parts should go in another plot
	quantProps = ['Astrogation Buffer Length','InfoCore Size',
		'AutoTerrain Tread Count','Polarity Sinks',
		'Cranial Uplink Bandwidth','Repulsorlift Motor HP',
		'Sonoreceptors']

	# if it's not empty, let's get going
	if (len(df2) > 0):
		df2 = df2[df2['column'].isin(quantProps)]
		c2 = alt.Chart(df2).mark_circle().encode(
			alt.X('column:N'),
			alt.Y('value:Q',scale=alt.Scale(domain=(-100, 100)))
		)
		partVis.write(c2)
	
	#show current time
	current_time=game.getGameTime().get('curtime')
	time_show.write('current time:    '+str(current_time))
	

	# set the default productivity
	robots = game.getRobotInfo()
	robots['Productivity']=-1000


	
	# if current_time >=50 and choose_part:
	# 	game.setPartInterest(choose_part)
	# 	lst=[i['column'] for i in hints['parts']]
	# 	corr_text.write(",".join(lst)+str(choose_part))
	# else:
	# 	corr_text.write(str(current_time)+ str(choose_part))
	# get the parts
		
	parthints_df = pd.DataFrame(game.getAllPartHints())
	parts_record.write("Part hint records: " + str(len(parthints_df)))
	df_parts=parthints_df.drop_duplicates().pivot(index='id',columns='column', values='value').reset_index()
	df_productivity=game.getRobotInfo().dropna(axis=0,subset=['Productivity'])
	robots.loc[df_productivity.index,'Productivity']=df_productivity['Productivity']

	cate_cols=["Arakyd Vocabulator Model","Axial Piston Model","Nanochip Model"]
	df_parts_d=df_parts.copy()
	for i in cate_cols:
		if i in df_parts_d.columns:
			df_parts_d=pd.get_dummies(data=df_parts_d, columns=[i])

	pd_pro_parts=robots.merge(df_parts_d,how='inner',left_on='id',right_on='id')
	pd_pro_parts=pd_pro_parts[pd_pro_parts['Productivity']!=-1000]
	#heatmap once a robot reaches the deadline
	if len(pd_pro_parts):
		corr_lst=[]
		var_lst=[]
		for i in list(df_parts_d.columns[1:]):
			df=pd_pro_parts.dropna(axis=0,subset=[i])
			try:
				df=df.loc[:,['Productivity',i]]
				corr, _ = pearsonr(df['Productivity'], df[i])
				var_lst.append(i)
				corr_lst.append(corr)
			except:
				continue

		df_corr=pd.DataFrame(data=np.array(var_lst), columns=["variable"])
		df_corr['corr']=corr_lst
		df_corr1=df_corr.set_index('variable').dropna().sort_values(by='corr')
		df_corr2=df_corr.dropna().sort_values(by='corr')
		# df_corr
		try:
			sns.set(font_scale=1)
			fig, ax = plt.subplots(figsize=(3,4))
			ax= sns.heatmap(df_corr1,annot=True)
			corrVis1.write(fig)
		except:
			pass

		#altair heatmap
		c3=alt.Chart(df_corr2).mark_rect().encode(
			y=alt.Y('variable:N',sort='-x'),
			x='corr:Q',
			color='corr:Q'
		)
		corrVis.write(c3)
		#assign 3 parts with top correlation coefficient to a variable
		choose_part=df_corr1.abs().head(3).index.tolist()
		df_choose_part=pd_pro_parts.loc[:,choose_part].reset_index().rename(columns={'index':'id'})







