import certifi
from django.shortcuts import render
from bs4 import BeautifulSoup as bs
from gnewsclient import gnewsclient
from heapq import nlargest
import lxml
from newspaper import Article, Config
import numpy as np
from random import randint
import requests
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import ssl
from string import punctuation
from time import sleep
from warnings import warn
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity

stopWords = list(set(stopwords.words('english')))

def cos_similarity(search_query_weights, tfidf_weights_matrix):
	
	cosine_distance = cosine_similarity(search_query_weights, tfidf_weights_matrix)
	similarity_list = cosine_distance[0]
  
	return similarity_list

def most_similar(similarity_list, ndocs=1):
	
	most_similar= []
  
	while ndocs > 0:
		tmp_index = np.argmax(similarity_list)
		most_similar.append(tmp_index)
		similarity_list[tmp_index] = 0
		ndocs -= 1

	return most_similar

def tf_idf(search_keys, docs):
  
	tfidf_vectorizer = TfidfVectorizer(stop_words=stopWords)
	tfidf_weights_matrix = tfidf_vectorizer.fit_transform(docs)
	search_query_weights = tfidf_vectorizer.transform(search_keys)
	
	return search_query_weights, tfidf_weights_matrix

# Create your views here.
def index(request):
    return render(request, 'index.html')



def search(request):
    if request.method == 'POST':
        search = request.POST['search']
        max_pages = 3
        final_result = []
        docs = []
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(certifi.where())
        ssl._create_default_https_context = context
        for page in range(0,max_pages):
            url = 'https://www.ask.com/web?q=' + search + "&qo=pagination&page=" + str(page)
            headers = {
                'User-Agent': 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
            }
            res = requests.get(url, allow_redirects=True, headers=headers)
            soup = bs(res.text, 'lxml')
            result_listings = soup.find_all('div', {'class': 'PartialSearchResults-item'})
            # uniqueURLs = set()
            for result in result_listings:
                result_title = result.find(class_='PartialSearchResults-item-title').text
                result_url = result.find('a').get('href')
                result_desc = result.find(class_='PartialSearchResults-item-abstract').text
                # session = requests.Session()
                # response = session.get(result_url)
                # result_cookies = len(session.cookies.get_dict())
                final_result.append((result_title, result_url, result_desc))

                if(result_url is not None):
                    res = requests.get(result_url, allow_redirects=True, headers=headers)

                    if(res is not None):
                        soup = bs(res.text, 'lxml')
                        texts = soup.find_all(text=True)
                        doc = u" ".join(text.strip() for text in texts if text.parent.name not in ['style', 'script', 'head', 'title', 'meta', '[document]'])
                        docs.append(doc)

        search_query_weights, tfidf_weights_matrix = tf_idf(search.split(), docs)
        similarity_list = cos_similarity(search_query_weights, tfidf_weights_matrix)
        ranks = most_similar(similarity_list, len(docs))

        toRender = {}
        j = 0
        for i in ranks:
            if(ranks[i] not in toRender):
                toRender[ranks[i]] = []
                toRender[ranks[i]].append(final_result[j])
            else:
                toRender[ranks[i]].append(final_result[j])
            j += 1

        final_list_toRender = [j for i in toRender.values() for j in i]

        context = {
            'final_result': final_list_toRender,
            'query': search
        }
        return render(request, 'search.html', context)
    else:
        return render(request, 'search.html')


def imageSearch(request):
    if request.method == 'POST':
        search = request.POST['imageSearch']
        max_pages = 8
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',}
        params = {
            "q": search,
            "tbm": "isch",                # image results
            "hl": "en",                   # language of the search
            "gl": "us",                   # country where search comes from
            "ijn": "0",                    # page number
        }
        images = []
        for page in range(0, max_pages):
            params['ijn'] = str(page)
            html = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=30)
            soup = bs(html.text, "lxml")
            for img in soup.select("img"):
                images.append(img['src'])
        context = {
            'images': images,
            'query': search
        }
        return render(request, 'imageSearch.html', context)
    else:
        return render(request, 'imageSearch.html')


def newsSearch(request):
    countries = ["Australia", "Botswana", "Canada", "Ethiopia", "Ghana", "India", "Indonesia", "Ireland", "Israel", "Kenya", "Latvia", "Malaysia", "Namibia", 
    "New Zealand", "Nigeria", "Pakistan", "Philippines", "Singapore", "South Africa", "Tanzania", "Uganda", "United Kingdom", "United States", "Zimbabwe", 
    "Czech Republic", "Germany", "Austria", 'Switzerland', 'Argentina', 'Chile', 'Colombia', 'Cuba', 'Mexico', 'Peru', 'Venezuela', 'Belgium ', 'France', 'Morocco', 'Senegal', 'Italy',
    'Lithuania', 'Hungary', 'Netherlands', 'Norway', 'Poland', 'Brazil', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Sweden', 'Vietnam', 'Turkey', 'Greece',
    'Bulgaria', 'Russia', 'Ukraine ', 'Serbia', 'United Arab Emirates', 'Saudi Arabia', 'Lebanon', 'Egypt', 'Bangladesh', 'Thailand', 'China', 'Taiwan', 'Hong Kong', 
    'Japan', 'Republic of Korea']
    topics = ["Business", "Technology", "Entertainment", "Sports", "Science", "Health"]
    selectParams = {
        'countries': countries,
        'topics': topics
    }
    if request.method == 'POST':
        client = gnewsclient.NewsClient()
        newsLocation = request.POST['country']
        newsTopic = request.POST['topics']
        search = {
            'country': newsLocation,
            'topic': newsTopic
        }
        # """
        # Possible values of news location :-
        # 'Australia', 'Botswana', 'Canada ', 'Ethiopia', 'Ghana', 'India ', 'Indonesia', 
        # 'Ireland', 'Israel ', 'Kenya', 'Latvia', 'Malaysia', 'Namibia', 'New Zealand', 
        # 'Nigeria', 'Pakistan', 'Philippines', 'Singapore', 'South Africa', 'Tanzania', 
        # 'Uganda', 'United Kingdom', 'United States', 'Zimbabwe', 'Czech Republic', 
        # 'Germany', 'Austria', 'Switzerland', 'Argentina', 'Chile', 'Colombia', 'Cuba', 
        # 'Mexico', 'Peru', 'Venezuela', 'Belgium ', 'France', 'Morocco', 'Senegal', 'Italy', 
        # 'Lithuania', 'Hungary', 'Netherlands', 'Norway', 'Poland', 'Brazil', 'Portugal', 
        # 'Romania', 'Slovakia', 'Slovenia', 'Sweden', 'Vietnam', 'Turkey', 'Greece', 
        # 'Bulgaria', 'Russia', 'Ukraine ', 'Serbia', 'United Arab Emirates', 'Saudi Arabia', 
        # 'Lebanon', 'Egypt', 'Bangladesh', 'Thailand', 'China', 'Taiwan', 'Hong Kong', 
        # 'Japan', 'Republic of Korea'
        
        # Possible values of news Topics :- 
        # Business, Technology, Entertainment, Sports, Science, Health
        # """

        client.location = newsLocation.lower()
        client.topic = newsTopic.lower()
        client.language = 'english'
        client.max_results = 20
        userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        config = Config()
        config.browser_user_agent = userAgent
        config.request_timeout = 30
        newsList = client.get_news()
        final_result = []
        for news in newsList:
            newsTitle = news['title']
            newsURL = news['link']
            newsArticle = Article(newsURL, config=config)
            newsArticle.download()
            newsArticle.parse()
            nlp = spacy.load('en_core_web_sm')
            doc = nlp(newsArticle.text)
            tokens = [token.text for token in doc]
            wordFrequencies = {}
            for word in doc:
                if word.text.lower() not in list(STOP_WORDS):
                    if word.text.lower() not in punctuation:
                        if word.text not in wordFrequencies.keys():
                            wordFrequencies[word.text] = 1
                        else:
                            wordFrequencies[word.text] += 1
            if len(wordFrequencies) == 0:
                continue
            maxFrequency = max(wordFrequencies.values())
            for word in wordFrequencies.keys():
                wordFrequencies[word] = wordFrequencies[word] / maxFrequency
            sentenceTokens = [sent for sent in doc.sents]
            sentenceScores = {}
            for sent in sentenceTokens:
                for word in sent:
                    if word.text.lower() in wordFrequencies.keys():
                        if sent not in sentenceScores.keys():
                            sentenceScores[sent] = wordFrequencies[word.text.lower()]
                        else:
                            sentenceScores[sent] += wordFrequencies[word.text.lower()]
            summaryPercentage = 0.1
            selectLength = int(len(sentenceTokens) * summaryPercentage)
            summary = nlargest(selectLength, sentenceScores, key=sentenceScores.get)
            finalSummary = [word.text for word in summary]
            summary = ''.join(finalSummary)
            final_result.append((newsTitle, newsURL, summary))
        context = {
            'final_result': final_result,
            'query': search,
            'selectParams': selectParams
        }
        return render(request, 'newsSearch.html', context)
    else:
        context = {
            'selectParams': selectParams
        }
        return render(request, 'newsSearch.html', context)


def videoSearch(request):
    if request.method == 'POST':
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        }
        search = request.POST['videoSearch']
        params = {
            "q": search,
            "cc": "ind" # language/country of the search
        }
        html = requests.get('https://www.bing.com/videos/search', params=params, headers=headers)
        soup = bs(html.text, 'lxml')
        final_result = []
        for result in soup.select('.mc_vtvc.b_canvas'):
            title = result.select_one('.b_promtxt').text
            #link = f"https://www.bing.com{result.select_one('.mc_vtvc_link')['href']}"
            link = result.select_one('.mc_vtvc_link')['href']
            if link[0] == '/':
                link = 'https://www.bing.com' + link
            views = 'ago'
            if result.select_one('.mc_vtvc_meta_row:nth-child(1) span:nth-child(1)') != None:
                views = result.select_one('.mc_vtvc_meta_row:nth-child(1) span:nth-child(1)').text
            date = '1st January, 2010'
            if result.select_one('.mc_vtvc_meta_row:nth-child(1) span+ span') != None:
                date = result.select_one('.mc_vtvc_meta_row:nth-child(1) span+ span').text
            video_platform = 'Bing'
            if result.select_one('.mc_vtvc_meta_row+ .mc_vtvc_meta_row span:nth-child(1)') != None:
                video_platform = result.select_one('.mc_vtvc_meta_row+ .mc_vtvc_meta_row span:nth-child(1)').text
            channel_name = ''
            if result.select_one('.mc_vtvc_meta_row_channel') == None:
                channel_name = 'Unknown'
            else:
                channel_name = result.select_one('.mc_vtvc_meta_row_channel').text
            viewsNumerical = 0
            if 'B' in views:
                viewsNumerical = float(views[:-7]) * 1000000000
            elif 'M' in views:
                viewsNumerical = float(views[:-7]) * 1000000
            elif 'K' in views:
                viewsNumerical = float(views[:-7]) * 1000
            elif 'ago' in views or not views.isdigit():
                viewsNumerical = 0
            else:
                viewsNumerical = float(views[:-6])
            viewsNumerical = int(viewsNumerical)
            if views == 'ago':
                views = ''
            final_result.append((title, link, channel_name, video_platform, date, views, viewsNumerical))
        final_result = sorted(final_result, key=lambda x: x[-1], reverse=True)
        context = {
            'final_result': final_result,
            'query': search
        }
        return render(request, 'videoSearch.html', context)
    else:
        return render(request, 'videoSearch.html')


def movieSearch(request):
    genres = ['Comedy', 'Sci-fi', 'Horror', 'Romance', 'Action', 'Thirller', 'Drama', 'Mystery', 
        'Crime', 'Animation', 'Adventure', 'Fantasy', 'Superhero']
    if request.method == 'POST':
        """
        comedy, sci-fi, horror, romance, action, thirller, drama, mystery, 
        crime, animation, adventure, fantasy, superhero
        """
        search = request.POST['genres']
        pages = np.arange(1, 100, 50)
        headers = {'Accept-Language': 'en-US,en;q=0.8'}
        final_result = []
        for page in pages:
            url = 'https://www.imdb.com/search/title?genres=' + search.lower() + '&start=' + str(page) + '&explore=title_type,genres&ref_=adv_prv'
            response = requests.get(url, headers=headers)
            #sleep(randint(8, 15))
            if response.status_code != 200:
                warn('Request: {}; Status code: {}'.format(requests, response.status_code))
            page_html = bs(response.text, 'html.parser')  
            movie_containers = page_html.find_all('div', class_ = 'lister-item mode-advanced')
            for container in movie_containers:
                if container.find('div', class_ = 'ratings-metascore') is not None:
                    title = container.h3.a.text
                    link = 'https://www.imdb.com' + container.find('a').get('href')
                    year = None
                    if container.h3.find('span', class_= 'lister-item-year text-muted unbold') is not None:
                        year = container.h3.find('span', class_= 'lister-item-year text-muted unbold').text
                    rating = None
                    if container.p.find('span', class_ = 'certificate') is not None:            
                        rating = container.p.find('span', class_= 'certificate').text
                    genre = []
                    if container.p.find('span', class_ = 'genre') is not None:
                        genre = container.p.find('span', class_ = 'genre').text.replace("\n", "").rstrip().split(',')
                    runtime = None
                    if container.p.find('span', class_ = 'runtime') is not None:
                        runtime = container.p.find('span', class_ = 'runtime').text
                    imdb_rating = 0.0
                    if float(container.strong.text) is not None:
                        imdb_rating = float(container.strong.text)
                    metascore = 0
                    if container.find('span', class_ = 'metascore').text is not None:
                        metascore = int(container.find('span', class_ = 'metascore').text)
                    rankScore = imdb_rating + metascore
                    final_result.append((title, link, year, rating, genre, runtime, rankScore))
        final_result = sorted(final_result, key=lambda x: x[-1], reverse=True)
        context = {
            'final_result': final_result,
            'query': search,
            'genres': genres
        }
        return render(request, 'movieSearch.html', context)
    else:
        context = {
            'genres': genres
        }
        return render(request, 'movieSearch.html', context)
