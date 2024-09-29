import streamlit as st
import re
from io import StringIO
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from collections import Counter
from wordcloud import WordCloud
import emoji
import time

# Function to parse WhatsApp chat
def parse_chat(data):
    message_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}[ \s]?[APMapm]{2}) - (.*?): (.*)'
    media_pattern = r'<Media omitted>'
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' 

    system_message_patterns = [
        r'Messages and calls are end-to-end encrypted', 
        r'Your security code with .* changed', 
        r'Tap to learn more'
    ]

    total_messages = 0
    total_words = 0
    media_shared = 0
    links_shared = 0
    user_messages = {}
    dates = []
    words = []
    emojis = []
    response_times = {}
    last_user = None
    last_time = None

    hours = []

    for line in data.splitlines():
        if not line.strip():
            continue
        if any(re.search(pattern, line) for pattern in system_message_patterns):
            continue

        match = re.match(message_pattern, line)
        if match:
            total_messages += 1
            message_time = match.group(1)
            user = match.group(2)
            message_content = match.group(3)

            message_datetime = pd.to_datetime(message_time, format='%d/%m/%y, %I:%M %p')
            hours.append(message_datetime.hour)

            if last_user is not None and last_user != user:
                response_time = (message_datetime - last_time).total_seconds() / 60
                if user not in response_times:
                    response_times[user] = []
                response_times[user].append(response_time)

            last_user = user
            last_time = message_datetime

            if user not in user_messages:
                user_messages[user] = 0
            user_messages[user] += 1

            date = pd.to_datetime(message_time.split(",")[0], format='%d/%m/%y')
            dates.append(date)

            message_words = message_content.split()
            words.extend(message_words)
            total_words += len(message_words)
            
            emojis_in_message = [char for char in message_content if char in emoji.EMOJI_DATA]
            emojis.extend(emojis_in_message)

            if re.search(media_pattern, message_content):
                media_shared += 1

            if re.search(url_pattern, message_content):
                links_shared += 1

    avg_response_times = {user: (sum(times) / len(times)) for user, times in response_times.items()}

    return total_messages, total_words, media_shared, links_shared, dates, user_messages, words, emojis, avg_response_times, hours

# Streamlit app
def main():
    st.title('📊 WhatsApp Chat Analyzer 📊')
    st.write("Analyze your WhatsApp chat and get statistics on total messages, words, media, and links shared.")

    # Placeholder for loading message
    loading_placeholder = st.empty()

    uploaded_file = st.file_uploader("📁 Upload your WhatsApp chat (.txt file)", type="txt")

    if uploaded_file is not None:
         # Show loading message and timer
        loading_placeholder.markdown("<h2 style='text-align: center;'>Waking up... Please wait!</h2>", unsafe_allow_html=True)
        timer_placeholder = loading_placeholder.empty()  # Create another placeholder for the timer

        # Set a timer for 5 seconds (adjust as needed)
        for i in range(5, 0, -1):
            timer_placeholder.markdown(f"<h3 style='text-align: center;'>App will be ready in {i} seconds...</h3>", unsafe_allow_html=True)
            time.sleep(1)  # Wait for 1 second

        # Clear the loading message
        loading_placeholder.empty()

        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        chat_data = stringio.read()

        total_messages, total_words, media_shared, links_shared, dates, user_messages, words, emojis, avg_response_times, hours = parse_chat(chat_data)

        # Display results with enhanced styling
        st.subheader("📈 **Chat Analysis Results** 📈")
        st.markdown(f"""
        <div style='display: flex; justify-content: space-around;'>
            <div style='background-color: #e0f7fa; padding: 20px; border-radius: 10px; width: 200px; text-align: center;'>
                <h2>Total Messages</h2>
                <p style='font-size: 24px; font-weight: bold;'>{total_messages}</p>
            </div>
            <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; width: 200px; text-align: center;'>
                <h2>Total Words</h2>
                <p style='font-size: 24px; font-weight: bold;'>{total_words}</p>
            </div>
            <div style='background-color: #fff3e0; padding: 20px; border-radius: 10px; width: 200px; text-align: center;'>
                <h2>Media Shared</h2>
                <p style='font-size: 24px; font-weight: bold;'>{media_shared}</p>
            </div>
            <div style='background-color: #fce4ec; padding: 20px; border-radius: 10px; width: 200px; text-align: center;'>
                <h2>Links Shared</h2>
                <p style='font-size: 24px; font-weight: bold;'>{links_shared}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Weekly and Monthly analysis
        st.subheader("📅 **Message Frequency Analysis**")
        df_dates = pd.DataFrame(dates, columns=['Date'])

        # Weekly messages
        df_dates['Weekday'] = df_dates['Date'].dt.day_name()
        weekly_chart = df_dates['Weekday'].value_counts().sort_index()

        # Plot weekly chart
        fig, ax = plt.subplots()
        weekly_chart.plot(kind='bar', color='skyblue', ax=ax)
        ax.set_title("Messages per Day of the Week")
        ax.set_xlabel("Day of the Week")
        ax.set_ylabel("Number of Messages")
        st.pyplot(fig)

        # Monthly messages
        df_dates['Month'] = df_dates['Date'].dt.strftime('%B %Y')
        monthly_chart = df_dates['Month'].value_counts().sort_index()

        # Plot monthly chart
        fig, ax = plt.subplots()
        monthly_chart.plot(kind='bar', color='lightgreen', ax=ax)
        ax.set_title("Messages per Month")
        ax.set_xlabel("Month")
        ax.set_ylabel("Number of Messages")
        st.pyplot(fig)

        # --- NEW SECTION: Messages by Year (Trend over time) ---        
        st.subheader("📅 **Chat Trend Over Time (Yearly)**")
        df_dates['Year'] = df_dates['Date'].dt.year
        yearly_chart = df_dates['Year'].value_counts().sort_index().reset_index()
        yearly_chart.columns = ['Year', 'Number of Messages']

        # Plot yearly chart using Plotly
        fig = px.line(yearly_chart, x='Year', y='Number of Messages', title='Messages per Year', markers=True)
        st.plotly_chart(fig)

        # --- NEW SECTION: Peak Time Analysis ---
        st.subheader("🕒 **Peak Time of Day Analysis**")
        df_hours = pd.DataFrame(hours, columns=['Hour'])

        df_hours['Hour'] = df_hours['Hour'].apply(lambda x: x % 12 if x % 12 != 0 else 12)

        peak_hours = df_hours['Hour'].value_counts().sort_index()

        # Plot peak time chart
        fig, ax = plt.subplots()
        peak_hours.plot(kind='bar', color='purple', ax=ax)
        ax.set_title("Messages per Hour of the Day (12-Hour Format)")
        ax.set_xlabel("Hour of the Day")
        ax.set_ylabel("Number of Messages")

        ax.set_xticks(range(1, 13))
        ax.set_xticklabels([str(i) for i in range(1, 13)])  
        st.pyplot(fig)

        # User Message Analysis (Pie Chart)
        st.subheader("💬 **Messages by User (Percentage)**")
        df_user = pd.DataFrame(list(user_messages.items()), columns=['User', 'Messages'])
        df_user['Percentage'] = (df_user['Messages'] / total_messages) * 100
        df_user['Display'] = df_user['User'] + " (" + df_user['Messages'].astype(str) + ") - " + df_user['Percentage'].round(2).astype(str) + "%"

        # Plot pie chart using Plotly
        fig = px.pie(df_user, names='Display', values='Messages', title='Messages by User (Percentage)', color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig)

        # Word Cloud for visual representation of frequently used words
        st.subheader("📝 **Word Cloud of Messages**")
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(words))
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)

        # Emojis Analysis
        st.subheader("😊 **Most Frequently Used Emojis**")
        emoji_counts = Counter(emojis)
        emoji_df = pd.DataFrame(emoji_counts.most_common(10), columns=['Emoji', 'Count'])

        # Display emoji count as a table
        st.write(emoji_df)

        # Average Response Times
        st.subheader("⏱️ **Average Response Times**")
        avg_response_times_df = pd.DataFrame(list(avg_response_times.items()), columns=['User', 'Average Response Time (minutes)'])
        
        # Custom CSS for DataFrame
        st.markdown("""
        <style>
        .dataframe th, .dataframe td {
            padding: 10px;
            text-align: center;
        }
        .dataframe th {
            background-color: #e0f7fa;
        }
        .dataframe tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .dataframe tr:hover {
            background-color: #ffe0b2;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display Average Response Times DataFrame with CSS
        st.dataframe(avg_response_times_df.style.set_table_attributes('class="dataframe"'))

        # Display Chat Word Frequencies
        st.subheader("📖 **Word Frequency Count**")
        word_count = Counter(words)
        most_common_words = word_count.most_common(10)
        word_df = pd.DataFrame(most_common_words, columns=['Word', 'Count'])
        st.write(word_df)

if __name__ == "__main__":
    main()
