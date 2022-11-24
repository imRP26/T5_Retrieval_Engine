from django.shortcuts import render
import requests
from bs4 import BeautifulSoup as bs

# Create your views here.
def index(request):
    return render(request, 'index.html')

def search(request):
    if request.method == 'POST':
        search = request.POST['search']
        max_pages = 10
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