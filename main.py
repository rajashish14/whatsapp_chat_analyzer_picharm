
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import pdfplumber
from docx import Document
import pandas as pd
import os
import preprocessor
import solution


def extract_text_from_file(uploaded_file):
   file_extension = uploaded_file.name.split(".")[-1].lower()
   temp_path = f"temp_uploaded.{file_extension}"

   with open(temp_path, "wb") as f:
      f.write(uploaded_file.getbuffer())

   try:
      if file_extension == "txt":
         with open(temp_path, "r", encoding="utf-8") as f:
            text = f.read()

      elif file_extension == "pdf":
         text = ""
         with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
               text += page.extract_text() + "\n"

      elif file_extension == "docx":
         doc = Document(temp_path)
         text = "\n".join([para.text for para in doc.paragraphs])

      elif file_extension in ["xls", "xlsx"]:
         df = pd.read_excel(temp_path)
         text = df.to_string()

      else:
         text = "Unsupported file format."

   except Exception as e:
      text = f"Error extracting text: {str(e)}"

   os.remove(temp_path)  # Clean up temporary file
   return text


st.sidebar.title("whatsApp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("📂 Choose a file", type=["txt", "csv", "pdf", "docx"])
if uploaded_file is not None:
   file_extension = uploaded_file.name.split(".")[-1]

   if uploaded_file is not None:
      data = extract_text_from_file(uploaded_file)

      if data.startswith("Error"):
         st.error(data)
      else:
         df = preprocessor.preprocess(data)
         st.subheader("📄 Processed Data Preview")
         st.dataframe(df)

   # fetch unique users...

   user_list = df['users_name'].unique().tolist()
   user_list.sort()
   user_list.insert(0,"Overall")
   selected_users = st.sidebar.selectbox("🔍 Show Analysis For", user_list)

   if st.sidebar.button("📊 Show Analysis"):
      num_message, num_words, num_media, num_links = solution.fetch_stats(selected_users, df)

      st.markdown("---")
      st.subheader("📊 Chat Summary")
      col1, col2, col3, col4 = st.columns(4)

      col1.metric(label="💬 Total Messages", value=num_message)
      col2.metric(label="📝 Total Words", value=num_words)
      col3.metric(label="📸 Media Shared", value=num_media)
      col4.metric(label="🔗 Links Shared", value=num_links)


      # Most Active users.....

      if selected_users == 'Overall':
         with st.container():
            dictionary = Counter(df['users_name'])
            most_common = dictionary.most_common(2)

            if most_common:
               most_active, most_active_count = most_common[0]
               second_active, second_active_count = most_common[1] if len(most_common) > 1 else ("-", 0)

               st.subheader("🏆 Most Active Users")
               col1, col2 = st.columns(2)
               with col1:
                  st.markdown(f"""
                   <div style="text-align:center">
                       <p style="font-size:16px; font-weight:bold;">🥇 Most Active</p>
                       <p style="font-size:14px;">{most_active} ({most_active_count} messages)</p>
                   </div>
                   """, unsafe_allow_html=True)

            with col2:
               st.markdown(f"""
                   <div style="text-align:center">
                       <p style="font-size:16px; font-weight:bold;">🥈 2nd Most Active</p>
                       <p style="font-size:14px;">{second_active} ({second_active_count} messages)</p>
                   </div>
                   """, unsafe_allow_html=True)

         # plotting bar chart between users and message counts
         users, message_counts = zip(*dictionary.items())
         # Convert to lists if needed
         users = list(users)
         message_counts = list(message_counts)
         st.title("Most Active Users in Chat")

         # Create a Matplotlib figure
         fig, ax = plt.subplots(figsize=(20, 10))
         ax.bar(users, message_counts, color='skyblue')

         # Labels and Title
         ax.set_xlabel("Users", fontsize=12)
         ax.set_ylabel("Message Count", fontsize=12)
         ax.set_title("Most Active Users in Chat", fontsize=14)

         # Rotate x-axis labels for better readability
         plt.xticks(rotation=45, ha="right")

         # Display the chart in Streamlit
         st.pyplot(fig)


      # sentiment analysis

      df['sentiment'] = solution.get_sentiment(selected_users, df)  # ✅ Corrected

      # Calculate sentiment distribution
      sentiment_counts = df['sentiment'].value_counts(normalize=True) * 100

      # Streamlit UI
      st.subheader(f"Sentiment Analysis for {selected_users}")
      st.write(f"🔵 Positive: {sentiment_counts.get('Positive', 0):.2f}%")
      st.write(f"🔴 Negative: {sentiment_counts.get('Negative', 0):.2f}%")
      st.write(f"⚪ Neutral: {sentiment_counts.get('Neutral', 0):.2f}%")

      # Pie Chart
      fig, ax = plt.subplots()
      ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', colors=['blue', 'red', 'gray'])
      ax.set_title(f"Sentiment Distribution for {selected_users}")
      st.pyplot(fig)

      # emoji counts and plot chart......

      emoji_counts = solution.count_emojis(df, selected_users)
      plt.rcParams['font.family'] = 'Segoe UI Emoji'

      if emoji_counts:
         st.subheader(f"Emoji Usage in {selected_users}")

         # Convert dictionary to list of tuples for plotting
         emoji_list, emoji_freq = zip(*emoji_counts.items())

         col1, col2 = st.columns(2)

         # Display top 10 emojis
         with col1:
            emoji_df = pd.DataFrame({"Emoji": emoji_list, "Count": emoji_freq})
            st.dataframe(emoji_df.sort_values("Count", ascending=False).head(10))

         # Plot emoji frequency as a bar chart
         with col2:
            fig, ax = plt.subplots()
            ax.bar(emoji_list[:10], emoji_freq[:10], color="orange")
            plt.xticks(rotation=45, fontsize=14)  # Rotate for better visibility
            ax.set_title("Top 10 Most Used Emojis")
            st.pyplot(fig)


      # most used word...

      most_used_word = solution.get_most_used_word(selected_users, df)
      df_freq = pd.DataFrame({
         "Word": list(most_used_word.keys()),
         "Count": list(most_used_word.values())
      })

      # Display Table in Streamlit
      with st.container():
         st.markdown("<h4 style='text-align:center;'>🥇 Most Used Words</h4>", unsafe_allow_html=True)
         st.dataframe(df_freq.sort_values("Count", ascending=False), use_container_width=True)


      # Activity map....

      col1, col2 = st.columns(2)

      # most busy days...
      with col1:
         st.subheader("📅 Most Busy Days")
         day_counts = df['day_name'].value_counts()

         fig, ax = plt.subplots(figsize=(10, 4))
         sns.barplot(x=day_counts.index, y=day_counts.values, hue=day_counts.index, palette="viridis", ax=ax, legend=False)
         ax.set_xlabel("Day of the Week", fontsize=30)
         ax.set_ylabel("Message Count", fontsize=30)
         ax.set_title("Most Busy Days", fontsize=40)
         st.pyplot(fig)


      # most active month....
      with col2:
         st.subheader("📆 Most Busy Months")
         month_counts = df['month_name'].value_counts()

         fig, ax = plt.subplots(figsize=(10, 4))
         sns.barplot(x=month_counts.index, y=month_counts.values, hue=month_counts.index, palette="coolwarm", ax=ax, legend=False)
         ax.set_xlabel("Month", fontsize=30)
         ax.set_ylabel("Message Count", fontsize=30)
         ax.set_title("Most Busy Months", fontsize=40)
         st.pyplot(fig)



      # Activity Heatmap (Hour vs. Day)
      st.subheader("⏳ Activity Heatmap")

      heatmap_data = df.groupby(['day', 'hour']).size().unstack().fillna(0).astype(int)

      fig, ax = plt.subplots(figsize=(12, 5))
      sns.heatmap(heatmap_data, cmap="Blues", linewidths=0.5, annot=True, fmt=".0f", ax=ax)

      ax.set_title("Activity Heatmap (Hour vs. Day)")
      ax.set_xlabel("Hour of the Day")
      ax.set_ylabel("Day of the Week")
      st.pyplot(fig)

      # Timeline....
      st.subheader("📅 Activity Timeline")

      weekly_timeline = df.groupby('day_name').size()
      monthly_timeline = df.groupby('month_name').size()

      col1, col2 = st.columns(2)

      # Weekly timeline.....
      with col1:
         fig1, ax1 = plt.subplots(figsize=(20, 10))
         ax1.plot(weekly_timeline.index, weekly_timeline.values, marker='o', color='b', linestyle='-')
         ax1.set_title("Weekly Activity Timeline", fontsize=40)
         ax1.set_xlabel("Date", fontsize=30)
         ax1.set_ylabel("Messages Count", fontsize=30)
         ax1.tick_params(axis='x', rotation=45)
         st.pyplot(fig1)

      # --- Monthly Timeline ---
      with col2:
         fig2, ax2 = plt.subplots(figsize=(20, 10))
         ax2.plot(monthly_timeline.index, monthly_timeline.values, marker='o', color='g', linestyle='-')
         ax2.set_title("Monthly Activity Timeline", fontsize=40)
         ax2.set_xlabel("Month", fontsize=30)
         ax2.set_ylabel("Messages Count", fontsize=30)
         ax2.tick_params(axis='x', rotation=45)
         st.pyplot(fig2)

      # wordcloud.....
      filtered_text = solution.get_wordcloud(selected_users, df)

      # Define stopwords
      stopwords = set(STOPWORDS)
      stopwords.update(["message", "edited", "deleted"])  # Add custom stopwords

      # Generate the word cloud
      wordcloud = WordCloud(
         width=1000,
         height=500,
         background_color="black",  # Use white for better contrast
         colormap="coolwarm",  # Custom color palette
         max_words=150,
         contour_color="black",  # Outline for the shape
         contour_width=1,
         stopwords=stopwords,
      ).generate(filtered_text)

      # Display the word cloud
      plt.figure(figsize=(50, 40))
      plt.imshow(wordcloud, interpolation="bilinear")
      plt.axis("off")  # Hide axes
      plt.title("Most Frequent Words in WhatsApp Chat", fontsize=40)
      st.pyplot(plt)


