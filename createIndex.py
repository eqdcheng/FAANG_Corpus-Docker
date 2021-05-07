from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import Match
from elasticsearch_dsl import Index, Document, Text, analyzer, tokenizer, Keyword, Date
import os 
import json
import datetime
import time


os.system("elasticsearch-7.10.2/bin/elasticsearch -d")
time.sleep(60)
connections.create_connection(hosts=['localhost'])


def get_corpus():
    #Docker is case sensitive
    with open(f'{os.getcwd()}Corpus/annotated_corpus.json', 'r') as j:
        corpus = json.loads(j.read())
    return corpus 

#basic white space tokenizer
reddit_analyzer = analyzer('reddit', tokenizer="whitespace", filter=["lowercase","stop"])

class RedditDocument(Document):

    title = Text(analyzer=reddit_analyzer)
    text = Text(analyzer=reddit_analyzer)
    subreddit = Keyword()
    ticker = Keyword()
    annotation = Keyword()
    annotated = Keyword()
    vader = Keyword()
    vader_score = Keyword()
    created_at = Date()


corpus = get_corpus()
# print("deleting index")
# reddit_index = Index("reddit")
# reddit_index.delete()

print('creating index')
reddit_index = Index("reddit")
reddit_index.document(RedditDocument)
reddit_index.create()
print('created index')


print('updating index')
for document in corpus:
    title = document['title']
    text = document['text']
    subreddit = document['subreddit']    
    ticker = document['equity']
    annotated = document['turkAnnotated']
    annotation = document['turkAnnotation']
    vader = document['vaderSentiment']
    vader_score = document['vaderCompound']
    dt = datetime.datetime.strptime(document['date'], '%Y-%m-%d %H:%M:%S')
    created_at = str(datetime.date(dt.year, dt.month, dt.day))
    doc = RedditDocument(title=title, 
                         text=text, 
                         subreddit=subreddit, 
                         ticker=ticker, 
                         annotated=annotated, 
                         annotation=annotation, 
                         vader=vader, 
                         vader_score=vader_score,
                         created_at=created_at)
    doc.meta.id = document['uuid']
    doc.save()

print('index stats')
print(reddit_index.stats())