import pandas as pd
import tweepy


def make_str(list_of_verbs):
    list_of_verbs = [a.lower() for a in list_of_verbs]
    if len(list_of_verbs) == 1:
        return list_of_verbs[0]
    else:
        return ' or '.join(set(list_of_verbs))
    

def get_hashtags(entity):
    try:
        hashtags = entity['hashtags']
    except:
        return None
    return [tag.get('tag') for tag in hashtags]


def query_tweets(bearer_token, query, max_results=100, limit=100, end_time=None):
    client = tweepy.Client(
        bearer_token=bearer_token,
        wait_on_rate_limit=True
    )

    tweet_fields=['text', 'created_at', 'entities', 'author_id']
    
    full_df = pd.DataFrame()
    
    counter = 0
    for batched_tweets in tweepy.Paginator(client.search_recent_tweets, query=query,
                                    tweet_fields=tweet_fields,
                                    expansions=['author_id'],
                                    user_fields=['username'],
                                    max_results=max_results,
                                    end_time=end_time):
        while counter < limit:
            users = batched_tweets.includes['users']
            users_df = pd.DataFrame(users, columns=['id','name','username'])
            data = batched_tweets.data
            data_df = pd.DataFrame(data)
            data_df["created_at"] = pd.to_datetime(data_df.created_at)
            data_df["hashtags"] = data_df["entities"].apply(lambda a: get_hashtags(a))
            data_df = data_df.merge(users_df, left_on="author_id", right_on="id", how="left")
            data_df.rename({"text": "tweet_text"}, axis=1, inplace=True)
            data_df.drop(["entities", "author_id", "id_x", "id_y"], axis=1, inplace=True)
            full_df = pd.concat([full_df, data_df], ignore_index=True)
            counter += max_results
        return full_df
