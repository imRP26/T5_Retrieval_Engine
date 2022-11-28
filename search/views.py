import certifi
from django.shortcuts import render
from bs4 import BeautifulSoup as bs
from gnewsclient import gnewsclient
from heapq import nlargest
import lxml
from newspaper import Article, Config
import requests
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import ssl
from string import punctuation


# Create your views here.
def index(request):
    return render(request, 'index.html')



def search(request):
    if request.method == 'POST':
        search = request.POST['search']
        max_pages = 5
        final_result = []
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(certifi.where())
        ssl._create_default_https_context = context
        for page in range(0,max_pages):
            url = 'https://www.ask.com/web?q=' + search + "&qo=pagination&page=" + str(page)
            #res = requests.get(url, verify=False)
            res = requests.get(url)
            soup = bs(res.text, 'lxml')
            result_listings = soup.find_all('div', {'class': 'PartialSearchResults-item'})
            uniqueURLs = set()
            for result in result_listings:
                result_title = result.find(class_='PartialSearchResults-item-title').text
                result_url = result.find('a').get('href')
                result_desc = result.find(class_='PartialSearchResults-item-abstract').text
                session = requests.Session()
                response = session.get(result_url)
                result_cookies = len(session.cookies.get_dict())
                final_result.append((result_title, result_url, result_desc, result_cookies))
        final_result = sorted(final_result, key=lambda x: x[-1])
        context = {
            'final_result': final_result,
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
    if request.method == 'POST':
        client = gnewsclient.NewsClient()
        search = request.POST['newsSearch']
        queryList = search.split()
        """
        Possible values of news location :-
        'Australia', 'Botswana', 'Canada ', 'Ethiopia', 'Ghana', 'India ', 'Indonesia', 
        'Ireland', 'Israel ', 'Kenya', 'Latvia', 'Malaysia', 'Namibia', 'New Zealand', 
        'Nigeria', 'Pakistan', 'Philippines', 'Singapore', 'South Africa', 'Tanzania', 
        'Uganda', 'United Kingdom', 'United States', 'Zimbabwe', 'Czech Republic', 
        'Germany', 'Austria', 'Switzerland', 'Argentina', 'Chile', 'Colombia', 'Cuba', 
        'Mexico', 'Peru', 'Venezuela', 'Belgium ', 'France', 'Morocco', 'Senegal', 'Italy', 
        'Lithuania', 'Hungary', 'Netherlands', 'Norway', 'Poland', 'Brazil', 'Portugal', 
        'Romania', 'Slovakia', 'Slovenia', 'Sweden', 'Vietnam', 'Turkey', 'Greece', 
        'Bulgaria', 'Russia', 'Ukraine ', 'Serbia', 'United Arab Emirates', 'Saudi Arabia', 
        'Lebanon', 'Egypt', 'Bangladesh', 'Thailand', 'China', 'Taiwan', 'Hong Kong', 
        'Japan', 'Republic of Korea'
        
        Possible values of news Topics :- 
        Business, Technology, Entertainment, Sports, Science, Health
        """
        newsTopic = queryList[-1]
        queryList.pop()
        newsLocation = ""
        for location in queryList:
            newsLocation += location
            newsLocation += ' '
        newsLocation = newsLocation.rstrip(newsLocation[-1])
        client.location = newsLocation.lower()
        client.topic = newsTopic.lower()
        client.language = 'english'
        client.max_results = 25
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
            'query': search
        }
        return render(request, 'newsSearch.html', context)
    else:
        return render(request, 'newsSearch.html')


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
