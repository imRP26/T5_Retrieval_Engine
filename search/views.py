from django.shortcuts import render
import requests
from bs4 import BeautifulSoup as bs


# Create your views here.
def index(request):
    return render(request, 'index.html')


"""
def search(request):
    if request.method == 'POST':
        search = request.POST['search']
        max_pages = 5
        final_result = []
        for page in range(0,max_pages):
            url = 'https://www.ask.com/web?q=' + search + "&qo=pagination&page=" + str(page)
            res = requests.get(url)
            soup = bs(res.text, 'lxml')
            result_listings = soup.find_all('div', {'class': 'PartialSearchResults-item'})
            
            for result in result_listings:
                result_title = result.find(class_='PartialSearchResults-item-title').text
                result_url = result.find('a').get('href')
                result_desc = result.find(class_='PartialSearchResults-item-abstract').text
                final_result.append((result_title, result_url, result_desc))
        context = {
            'final_result': final_result
        }
        return render(request, 'search.html', context)
    else:
        return render(request, 'search.html')
"""
def search(request):
    if request.method == 'POST':
        search = request.POST['search']
        searchList = search.split()
        searchType = searchList[0]
        
        if searchType == 'text':
            search = search[5:]
            maxPages = 5
            final_result = []
            for page in range(maxPages):
                url = 'https://www.ask.com/web?q=' + search + "&qo=pagination&page=" + str(page)
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
                    #print (result_cookies)
                    final_result.append((result_title, result_url, result_desc, result_cookies))
            #print (type(final_result)) -> <class 'list'>
            #print (type(final_result[0])) -> <class 'tuple'>
            #final_result = final_result.sort(key=lambda x: x[-1])
            final_result = sorted(final_result, key=lambda x: x[-1])
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
        
        elif searchType == 'news':
            newsWeb = 'https://www.cbn.com/'
            news = build(newsWeb, memoize_articles=False)
            nltk.download('punkt')
            final_result = []
            for article in news.articles:
                article1 = article
                articleTitle = article1.title
                if articleTitle == None:
                    articleTitle = 'India News' 
                articleURL = article1.url
                article1.download()
                article1.parse()
                article1.nlp()
                articleSummary = article1.summary
                final_result.append((articleTitle, articleURL, articleSummary))
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
        
        elif searchType == 'videos':
            search = search[7:]
            headers = {
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            }
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
                views = result.select_one('.mc_vtvc_meta_row:nth-child(1) span:nth-child(1)').text
                date = ''
                if result.select_one('.mc_vtvc_meta_row:nth-child(1) span+ span') == None:
                    date = '1st January, 2022'
                else:
                    date = result.select_one('.mc_vtvc_meta_row:nth-child(1) span+ span').text
                video_platform = result.select_one('.mc_vtvc_meta_row+ .mc_vtvc_meta_row span:nth-child(1)').text
                channel_name = ''
                if result.select_one('.mc_vtvc_meta_row_channel') == None:
                    channel_name = 'YouTuber'
                else:
                    channel_name = result.select_one('.mc_vtvc_meta_row_channel').text
                final_result.append((title, link, views, date, video_platform, channel_name))
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
        
        elif searchType == 'related_question':
            headers = {
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
            }
            searchQuery = search[17:]
            search_url = 'https://www.bing.com/search?q=' + searchQuery + '&hl=en'
            #html = requests.get('https://www.bing.com/search?q=lion king&hl=en', headers=headers)
            html = requests.get(search_url, header=headers)
            soup = bs(html.content, 'lxml')
            final_result = []
            for related_question in soup.select('#relatedQnAListDisplay .df_topAlAs'):
                question = related_question.select_one('.b_1linetrunc').text
                snippet = related_question.select_one('.rwrl_padref').text
                title = related_question.select_one('#relatedQnAListDisplay .b_algo p').text
                link = related_question.select_one('#relatedQnAListDisplay .b_algo a')['href']
                displayed_link = related_question.select_one('#relatedQnAListDisplay cite').text
                final_result.append((question, snippet, title, link, displayed_link))
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
        
        elif searchType == 'related_search':
            headers = {
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
            }
            searchQuery = search[15:]
            search_url = 'https://www.bing.com/search?q=' + searchQuery + '&hl=en'
            html = requests.get(search_url, header=headers)
            #html = requests.get('https://www.bing.com/search?q=lion king&hl=en', headers=headers)
            soup = bs(html.content, 'lxml')
            final_result = []
            for related_search in soup.select('.b_rs ul li'):
                title = related_search.text
                #link = f"https://www.bing.com{related_search.a['href']}"
                link = related_search.a['href']
                final_result.append((title, link))
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
        
        elif searchType == 'research':
            searchQuery = search[9:]
            searchQueryList = searchQuery.split()
            query1 = searchQueryList[:-1]
            
            source1 = searchQueryList[-1]
            print (query1, source1)
            final_result = []
            params = {
                "q": source1,  # search query
                "hl": "en",                         # language of the search
                "gl": "us",                         # country of the search
                "start": 0
            }
            headers = {
                "User-Agent": 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            }
            while True:
                html = requests.get("https://scholar.google.com/scholar", params=params, headers=headers, timeout=100)
                selector = Selector(html.text)
                for result in selector.css(".gs_r.gs_scl"):
                    title = result.css(".gs_rt").xpath("normalize-space()").get()
                    link = result.css(".gs_rt a::attr(href)").get()
                    result_id = result.attrib["data-cid"]
                    snippet = result.css(".gs_rs::text").get()
                    publication_info = result.css(".gs_a").xpath("normalize-space()").get()
                    cite_by_link = f'https://scholar.google.com/scholar{result.css(".gs_or_btn.gs_nph+ a::attr(href)").get()}'
                    all_versions_link = f'https://scholar.google.com/scholar{result.css("a~ a+ .gs_nph::attr(href)").get()}'
                    related_articles_link = f'https://scholar.google.com/scholar{result.css("a:nth-child(4)::attr(href)").get()}'
                    pdf_file_title = result.css(".gs_or_ggsm a").xpath("normalize-space()").get()
                    pdf_file_link = result.css(".gs_or_ggsm a::attr(href)").get()
                    final_result.append((title, link, result_id, snippet, publication_info, cite_by_link, 
                                         all_versions_link, related_articles_link, pdf_file_title, pdf_file_link))
                if selector.css(".gs_ico_nav_next").get():
                    params["start"] += 10
                else:
                    break
            #scrape_conference_publications(query=query1, source=list(source1))
            context = {
                'final_result': final_result
            }
            return render(request, 'search.html', context)
    else:
        return render(request, 'search.html')


def imageSearch(request):
    if request.method == 'POST':
        search = request.POST['imageSearch']
        max_pages = 5
        final_result = []
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