from fastapi import FastAPI
import uvicorn
from fastapi.responses import FileResponse, HTMLResponse
from collections import defaultdict
import aiofiles

from elasticsearch import Elasticsearch
from elasticsearch_dsl.query import Match
from elasticsearch_dsl import Index, Document, Text, analyzer, tokenizer, Keyword, Date, Search
from elasticsearch_dsl.connections import connections
from datetime import datetime, timezone, date
import createIndex

app = FastAPI()
connections.create_connection(hosts=['localhost'])
reddit_index = Index("reddit")

def call_elastic_search(text, start_date, end_date, subreddit, sentiment):
    """
    Takes a natural query search result, and gets relevant results 
    from Elastic Search
    """
    s = reddit_index.search()
    s = s.query(Match(text=text))
    s = s[:500]
    s = s.filter('range', **{'created_at': {"from": start_date, "to": end_date}})
    
    if subreddit:
        s = s.filter('term', **{'subreddit': subreddit})

    if sentiment:

        sentiment = sentiment.split('_')

        if sentiment[0] == 'vader':

            if sentiment[1] == 'positive':
                #s = s.query(Match(vaderSentiment="Positive"))
                s = s.filter('term', **{'vader': 'Positive'})
                #s = s.filter('term', **{'vaderSentiment':"Positive"})
            else:
                s = s.filter('term', **{'vader': 'Negative'})
                #s = s.query(Match(vaderSentiment="Negative"))
                #s = s.filter('term', **{'vaderSentiment':"Negative"})
 
        if sentiment[0] =='turk':
            if sentiment[1] == 'positive':
                s = s.filter('term', **{'annotation': "INCREASE"})
            
            if sentiment[1] == 'neutral':
                s = s.filter('term', **{'annotation': "NEUTRAL"})
            
            if sentiment[1] == 'negative':
                s = s.filter('term', **{'annotation': "DECREASE"})
            
        pass
  
    response = s.execute()
    return response 

def create_row(response):
    '''from a list of items, create a HTML unordered list of cells with one hit response in each cell'''
    S = []
    for hit in response:
        S.append("<li><h3>" + str(hit.title) + "</h3>")
        S.append("<h4>" +str("Subreddit: ") + str(hit.subreddit) + "</h4>")
        S.append("<h4>" +str("Date Created: ") + str(hit.created_at) + "</h4>")
        S.append("<h4>" +str("Vader Sentiment: ") + str(hit.vader) + "</h4>")
        S.append("<h4>" +str("Vader Compound Score: ") + str(hit.vader_score) + "</h4>")
        S.append("<h4>" +str("Turk Sentiment: ") + str(hit.annotation) + "</h4>")
        S.append("<p>" + str(hit.text) + "</p></li>")
    return "".join(S)

def put_in_list(response):
    '''represent a dictionary as an HTML table, with the first row as keys, and the second row as values'''
    header = '<br><br><br><br><br><br><h1>$MANA vs. FAANG Corpus$</h1>'
    search = '<input type="search" id="search-input" class="search" placeholder="Search a MANA or FAANG stock..." autocomplete="off" onkeydown="search(this)">'
    search_again = '<a href="/">Search again</a>'
    generator = '<p class="result">Generating Results...</p>'
    footer = '<div class=footer></div>'
    return header +search_again + generator + '<ul class="res clearfix">' + create_row(response) + "</ul>"


@app.get("/")
def start():
    '''just returns the string hello world'''
    return FileResponse('landing.html')

@app.get("/{filename}")
def get_file(filename):
    '''just returns the string hell world'''
    return FileResponse(filename)

@app.get("/search/")
def get_search_results(text, start_date=False, end_date=False, subreddit=False, sentiment=False):
    response = call_elastic_search(text, start_date, end_date, subreddit, sentiment)
    return HTMLResponse(put_in_list(response))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port = 9999, debug=True)

