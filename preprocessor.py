import re
import pandas as pd
def preprocess(data):
    pattern = r"\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?[ap]m\s-\s"
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    df = pd.DataFrame({'user_messages': messages, 'messages_dates': dates})
    df['messages_dates'] = pd.to_datetime(df['messages_dates'], format='%d/%m/%Y, %I:%M %p - ')
    df.rename(columns={'messages_dates': 'date'}, inplace=True)
    users_name = []
    messages = []
    for message in df['user_messages']:
        name = re.split(r"([\s\S]+?):\s", message, 1)
        if name[1:]:
            users_name.append(name[1])
            messages.append(name[2])
        else:
            users_name.append('group_notification')
            messages.append(name[0])

    df['users_name'] = users_name
    df['messages'] = messages
    df.drop(columns=['user_messages'], inplace=True)


    df['year'] = df['date'].dt.year
    df['month_name'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    df = df[df['users_name'] != "group_notification"]
    df.reset_index(drop=True, inplace=True)
    df.drop(columns=['date'], inplace=True)

    return df