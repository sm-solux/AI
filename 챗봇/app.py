from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
import os
import sys
import urllib.request
from urllib.parse import quote
import re
import time
import random
from bs4 import BeautifulSoup as bs

app = Flask(__name__)


# 취향별 추천
def returnPreference(movies_name):
    movie_list = movies_name.split(", ")
    
    movie_cd_list = []
    director_list = []
    selected_movie_list = []

    for movie in movie_list:
        movie_cd_url = 'https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key='+키+'&movieNm='+movie[:-5]
        
        res = requests.get(movie_cd_url)
        text = res.text
        d = json.loads(text)
        if d['movieListResult']['totCnt'] > 1:    # 동명의 영화가 있을 경우
            item_year = movie[-4:]   # 개봉연도로 구분
            for item in d['movieListResult']['movieList']:
                if item_year == item['openDt'][:4]:
                    movie_cd_list.append([item['movieCd'],
                              item['movieNm'],
                              item['openDt'][:4]])
                    selected_movie_list.append(item['movieNm'])
        if d['movieListResult']['totCnt'] == 1:
            for item in d['movieListResult']['movieList']:
                movie_cd_list.append([item['movieCd'],
                    item['movieNm'],
                    item['openDt'][:4]])
                selected_movie_list.append(item['movieNm'])
    
    movie_cdlist_df = pd.DataFrame(movie_cd_list)
    movie_cdlist_df.columns = ['movieCd', 'movieNm','openYr']
    
    
    movie_detail_list = []
    movie_director_list = []
    movie_cast_list = []    # 한 영화당 최대 10명의 배우를 추출하여 저장한 리스트
    direct_list = []
    movie_mainactor_list = []    # 한 영화당 최대 2명(주인공)의 배우를 추출하여 저장한 리스트
    movie_genre_list = [] 

    actor_list = []              # 5개 영화의 movie_cast_list을 모은 것
    mainactor_list = []          # 5개 영화의 movie_mainactor_list을 모은 것
    genre_list = []
    
    movie_actor_list = [[] for i in range(0,5)]
    movie_direc_list = [[] for i in range(0,5)]
    j=0
    
    for movieCd in movie_cdlist_df['movieCd']:
        movie_director_list.clear()
        movie_cast_list.clear()
        movie_mainactor_list.clear()
        movie_genre_list.clear()

        actor_list_url = 'https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key='+키+'&movieCd='+movieCd
        res = requests.get(actor_list_url)
        text = res.text
        d = json.loads(text)
        
        for direc in d['movieInfoResult']['movieInfo']['directors']:
            movie_director_list.append(direc['peopleNm'])
        direct_list+=movie_director_list
        
        for cast in d['movieInfoResult']['movieInfo']['actors']:
            if len(movie_mainactor_list) < 2:
                movie_mainactor_list.append(cast['peopleNm'])
            if len(movie_cast_list) <= 9:
                movie_cast_list.append(cast['peopleNm'])
                
        for genr in d['movieInfoResult']['movieInfo']['genres']:
            movie_genre_list.append(genr['genreNm'])
        
        actor_list += movie_cast_list
        mainactor_list += movie_mainactor_list
        genre_list += movie_genre_list

        j+=1
        
    actor_dict = dict()
    for i in actor_list:
        if i not in actor_dict:
            actor_dict[i]=1
        else:
            actor_dict[i] = actor_dict[i]+1

    mainactor_dict = dict()
    for i in mainactor_list:
        if i not in mainactor_dict:
            mainactor_dict[i]=1
        else:
            mainactor_dict[i] = mainactor_dict[i]+1

    prefer_actor_list = []
    for key, value in actor_dict.items():
        if value > 1:
            prefer_actor_list.append(key)
    if len(prefer_actor_list)<5:
        while True:
            actor = random.choice(mainactor_list)
            if actor not in prefer_actor_list:
                prefer_actor_list.append(actor)
            if len(prefer_actor_list)==5:
                break
    
    actor_code = []
    filmo_list = []
    final_filmo_list = []
    for prefer_actor in prefer_actor_list:
        actor_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key='+키+'&peopleNm='+prefer_actor        
        res = requests.get(actor_list_url)
        text = res.text
        d = json.loads(text)

        for actor in d['peopleListResult']['peopleList']:
            final_filmo_list.clear()
            if actor['repRoleNm'] == '배우' and actor['peopleNmEn']!= "":
                filmo_list = actor['filmoNames'].split("|")
                for filmo in filmo_list:
                    if filmo not in selected_movie_list:
                        final_filmo_list.append(filmo)
                actor_code.append([actor['peopleCd'], actor['peopleNm'],actor['peopleNmEn'],
                         actor['repRoleNm'], final_filmo_list[:5]])
    
    actor_code_df = pd.DataFrame(actor_code)
    actor_code_df.columns = ['peopleCd','peopleNm','peopleNmEn','repRoleNm','filmoNames']
    
    genre_dict = dict()
    for i in genre_list:
        if i not in genre_dict:
            genre_dict[i]=1
        else:
            genre_dict[i]=genre_dict[i]+1

    genre_df = pd.DataFrame(genre_dict.items())
    genre_df.columns=['genres', 'number']
    
    gen=dict()
    gen=genre_df['genres']
    gg=gen.values
    
    recom_genre=[]
    recom_genre=genre_df[genre_df['number']>1]
    recom_genre_list=recom_genre['genres']
    recom_genre_list=recom_genre_list.values
    
    genre_search=[]
    movieID=[]
    prdY=[]
    odt=[]
    movieN=[]
    moviepeople=[]

    for i in range(len(final_filmo_list)):
        genre_search_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key='+키+'&movieNm='+final_filmo_list[i]
        res = requests.get(genre_search_url)
        text = res.text
        d = json.loads(text)

        if d['movieListResult']['totCnt'] > 1:
            for item in d['movieListResult']['movieList']:
                movieID.append(item['movieCd'])

        if d['movieListResult']['totCnt'] == 1:        
            for item in d['movieListResult']['movieList']:
                genre_search.append([item['movieNm'], item['genreAlt']])
            
    for i in range(len(movieID)):
        id_search_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key'+키+'&movieCd='+movieID[i]
        res = requests.get(id_search_url)
        text = res.text
        d = json.loads(text)
    
        dd=d['movieInfoResult']['movieInfo']
        for item in d['movieInfoResult']['movieInfo']['actors']:
            moviepeople=item['peopleNm']
            if moviepeople in prefer_actor_list:
                movieN.append(dd['movieNm'])
                prdY.append(dd['prdtYear'])
                odt.append(dd['openDt'])

    for i in range(len(movieN)):
        duplit_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key='+키+'&movieNm='+movieN[i]
        res = requests.get(duplit_url)
        text = res.text
        d = json.loads(text)
    
        for item in d['movieListResult']['movieList']:
            if item['openDt']==odt[i]:
                genre_search.append([item['movieNm'], item['genreAlt']])
                break
            if item['prdtYear']==prdY[i]:
                genre_search.append([item['movieNm'], item['genreAlt']])

    pre_recom_pd=pd.DataFrame(genre_search)
    pre_recom_pd.columns=['movieNm', 'genres']
    recom_genre=dict()
    real=dict()
    for i in range(len(recom_genre_list)):
        recom_genre=pre_recom_pd[pre_recom_pd['genres'].str.contains(recom_genre_list[i])]['movieNm']
        real.update(recom_genre)
    recommendation_list=[]
    for key, value in real.items():
        recommendation_list.append(value)

    return recommendation_list[:3]


# 감독 코드 추출
def returnDire(director_name):
    director_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key='+키+'&peopleNm='+director_name    
    res = requests.get(director_list_url)
    text = res.text
    d = json.loads(text)
    
    # 해당 감독의 정보 리스트 생성
    director_list = []
    filmo_list = []
    for director in d['peopleListResult']['peopleList']:
        if director['repRoleNm'] == '감독':
            filmo_list = director['filmoNames'].split('|')
            director_list.append([director['peopleCd'],director['peopleNm'],director['peopleNmEn'], director['repRoleNm'],filmo_list])
            
    # 해당 감독의 정보 데이터프레임 생성
    director_df = pd.DataFrame(director_list)
    director_df.columns = ['peopleCd','peopleNm','peopleNmEn','repRoleNm','filmoNames']
    
    director_code = director_df['peopleCd'][0]
    return director_code


# 영화 코드 추출
def returnMovie(director_code):
    movie_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleInfo.json?key='+키+'&peopleCd='+director_code    
    res = requests.get(movie_url)
    text = res.text
    d = json.loads(text)
    
    # 해당 감독 코드의 영화 코드 리스트 생성
    movieCd_list = []
    for movie in d['peopleInfoResult']['peopleInfo']['filmos']:
        if movie['moviePartNm'] == '감독':
            movieCd_list.append([movie['movieCd'], movie['movieNm']])
    
    movieCd_df = pd.DataFrame(movieCd_list)
    movieCd_df.columns = ['movieCd', 'movieNm']
    
    return movieCd_df


# 평점 추출
def returnRating(director_name, movieCd_df):
    # 네이버 API 사용
    client_id = your_id
    client_secret = your_pw
    
    film_list = []
    for movieNm in movieCd_df['movieNm']:
        time.sleep(0.1)
        encText = urllib.parse.quote(movieNm)
        url = "https://openapi.naver.com/v1/search/movie.json?query=" + encText + "&display=100" # json 결과
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        
        if(rescode==200):
            response_body = json.load(response)
            film_list.append(response_body)
        else:
            print("Error Code:" + rescode)
    
    film_df = pd.DataFrame(film_list)
    film_df.astype({'display': int})
    
    rating_list = []
    for i in range(film_df.shape[0]):
        for j in range(film_df['display'][i]):
            if director_name in film_df['items'][i][j]['director']:
                rating_list.append([film_df['items'][i][j]['title'].replace("<b>","").replace("</b>",""),film_df['items'][i][j]['link'],film_df['items'][i][j]['image'], film_df['items'][i][j]['subtitle'].replace("<b>","").replace("</b>",""), film_df['items'][i][j]['pubDate'],film_df['items'][i][j]['director'],film_df['items'][i][j]['actor'],film_df['items'][i][j]['userRating']])
    
    rating_df = pd.DataFrame(rating_list)
    rating_df.columns=['movieNm','link','image','submovieNm','pubDate','director','actor','userRating']
    rating_df = rating_df.drop_duplicates(['movieNm'], keep='first', ignore_index=True)
    rating_df_sorted = rating_df.sort_values(by=['userRating'], axis=0, ascending=False)
    final_recommendation = rating_df_sorted.head(5)

    final_list = final_recommendation.values.tolist()
    print(final_list)
    return final_list


def nationMovie(nation_name):
  nation_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/code/searchCodeList.json?key='+키+'&comCode=2204'
  res = requests.get(nation_list_url)
  text = res.text
  m = json.loads(text)
  for i in range(len(m['codes'])):
    if m['codes'][i]['korNm']==nation_name:
      nation_code=m['codes'][i]['fullCd']
      break

  movie_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key='+키+'&itemPerPage=20&repNationCd='+ str(nation_code) #50개 해봄
  res = requests.get(movie_list_url)
  text = res.text
  d = json.loads(text)

  movie_list = []


  for movie in d['movieListResult']['movieList']:
    movie['repNationNm'] ==nation_name
    movie_list.append([movie['movieNm']])
    
    
  movie_df = pd.DataFrame(movie_list)
  movie_df.columns = ['movieNm']  
  movielist=movie_df['movieNm'].tolist()
    
  #네이버 평점
  client_id = "5ujvhVMfhcKiunU70W0w"
  client_secret = "BwcbJNwH8b"

  film_list = []
  for movieNm in movie_df['movieNm']:
    time.sleep(0.1)
    encText = urllib.parse.quote(movieNm)
    url = "https://openapi.naver.com/v1/search/movie.json?query=" + encText + "&display=100" # json 결과
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):   
      response_body = json.load(response)
      film_list.append(response_body)
    else:
      print("Error Code:" + rescode)
  film_df = pd.DataFrame(film_list)
  film_df.astype({'display': int})

  rating_list = []
  #영화제목 포스터 사진 크롤링
  for i in range(film_df.shape[0]):
    for j in range(film_df['display'][i]):
      k=film_df['items'][i][j]['title'].replace("<b>","").replace("</b>","")
      if k in movielist:
        rating_list.append([film_df['items'][i][j]['title'].replace("<b>","").replace("</b>",""),film_df['items'][i][j]['link'],film_df['items'][i][j]['image'],
                            film_df['items'][i][j]['subtitle'].replace("<b>","").replace("</b>",""),
                            film_df['items'][i][j]['pubDate'],film_df['items'][i][j]['actor'],film_df['items'][i][j]['userRating']])
            
  rating_df = pd.DataFrame(rating_list)
  rating_df.columns=['movieNm','link','image','submovieNm','pubDate','actor','userRating']
  rating_df = rating_df.drop_duplicates(['movieNm'], keep='first', ignore_index=True)
  rating_df_sorted = rating_df.sort_values(by=['userRating'], axis=0, ascending=False)
    
  final_recommendation = rating_df_sorted.head(5)
  final_list = final_recommendation.values.tolist()
  return final_list


def actorMovie(actor_name): 
  actor_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key='+키+'&peopleNm='+str(actor_name)
  res = requests.get(actor_list_url)
  text = res.text
  d = json.loads(text)

  actor_list = []
  filmo_list = []

  for actor in d['peopleListResult']['peopleList']:
    if actor['repRoleNm'] == '배우':
      filmo_list = actor['filmoNames'].split('|')
      actor_list.append([actor['peopleCd'],actor['peopleNm'],actor['peopleNmEn'],
                      actor['repRoleNm'],filmo_list])
      actor_name = actor['peopleNm']

  actor_df = pd.DataFrame(actor_list)
  actor_df.columns = ['peopleCd','peopleNm','peopleNmEn','repRoleNm','filmoNames']

  movieCd_list = []
  for actor in actor_df['peopleCd']:
    movie_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleInfo.json?key='+키+'&peopleCd='+actor
    res = requests.get(movie_url)
    text = res.text
    d = json.loads(text)
    for movie in d['peopleInfoResult']['peopleInfo']['filmos']:
      movieCd_list.append([movie['movieCd'], movie['movieNm']])
  movieCd_df = pd.DataFrame(movieCd_list)
  movieCd_df.columns = ['movieCd', 'movieNm']

  client_id = "5ujvhVMfhcKiunU70W0w"
  client_secret = "BwcbJNwH8b"

  film_list = []
  for movieNm in movieCd_df['movieNm']:
    time.sleep(0.1)
    encText = urllib.parse.quote(movieNm)
    url = "https://openapi.naver.com/v1/search/movie.json?query=" + encText + "&display=100" # json 결과
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
      response_body = json.load(response)
      film_list.append(response_body)
    else:
      print("Error Code:" + rescode)
    
  film_df = pd.DataFrame(film_list)
  film_df.astype({'display': int})
  rating_list = []
#for film in film_df['items']:
  for i in range(film_df.shape[0]):
    for j in range(film_df['display'][i]):
      if actor_name in film_df['items'][i][j]['actor']:
        rating_list.append([film_df['items'][i][j]['title'].replace("<b>","").replace("</b>",""),film_df['items'][i][j]['link'],film_df['items'][i][j]['image'],
                            film_df['items'][i][j]['subtitle'].replace("<b>","").replace("</b>",""),
                            film_df['items'][i][j]['pubDate'],film_df['items'][i][j]['actor'],film_df['items'][i][j]['userRating']])
            
  rating_df = pd.DataFrame(rating_list)
  rating_df.columns=['movieNm','link','image','submovieNm','pubDate','actor','userRating']
  rating_df = rating_df.drop_duplicates(['movieNm'], keep='first', ignore_index=True)
  rating_df_sorted = rating_df.sort_values(by=['userRating'], axis=0, ascending=False)
    
  final_recommendation = rating_df_sorted.head(5)
  final_list = final_recommendation.values.tolist()
  return final_list


# 감독별 추천
@app.route('/api/directorInput', methods=['POST'])
def directorInput():
    body = request.get_json()  # body(SkillPayload)
    print(body)  # SkillPayload 출력
    
    director_name = body["action"]["detailParams"]["director_name"]["value"]
    
    dC = returnDire(director_name)
    movieDF = returnMovie(dC)
    filmo_list = returnRating(director_name, movieDF)
    
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": filmo_list[0][0],
                                "description": filmo_list[0][3] + ", " + filmo_list[0][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[0][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[0][1]
                                    }
                                ]
                            },
                            {
                                "title": filmo_list[1][0],
                                "description": filmo_list[1][3] + ", " + filmo_list[1][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[1][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[1][1]
                                    }
                                ]
                            },
                            {
                                "title": filmo_list[2][0],
                                "description": filmo_list[2][3] + ", " + filmo_list[2][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[2][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[2][1]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


# 예매순
@app.route('/api/reserve', methods=['POST'])
def reserve():
    body = request.get_json()  # body(SkillPayload)
    print(body)  # SkillPayload 출력
    
    url = "https://movie.naver.com/movie/running/current.naver?view=list&tab=normal&order=reserve"
    
    res = requests.get(url)
    html = res.text
    soup = bs(html, "html.parser")

    reserve_list = []
    for i in range(1, 4, 1):
        title = soup.select_one("ul.lst_detail_t1 > li:nth-child(" + str(i) + ") > dl.lst_dsc > dt.tit > a")
        exp = soup.select_one("ul.lst_detail_t1 > li:nth-child(" + str(i) + ") > dl.lst_dsc > dd.star > dl.info_exp > dd > div.b_star > span.num")
        img = soup.select_one("ul.lst_detail_t1 > li:nth-child(" + str(i) + ") > div.thumb > a > img")
        link = soup.select_one("ul.lst_detail_t1 > li:nth-child(" + str(i) + ") > dl.lst_dsc > dd.info_t1 > div.btn_area > a")
        
        reserve_list.append([title.text, exp.text + "%", img["src"], "https://movie.naver.com" + link["href"]])
    
    print(reserve_list)
    
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": reserve_list[0][0],
                                "description": reserve_list[0][1],
                                "thumbnail": {
                                    "imageUrl": reserve_list[0][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "예매하기",
                                        "webLinkUrl": reserve_list[0][3]
                                    }
                                ]
                            },
                            {
                                "title": reserve_list[1][0],
                                "description": reserve_list[1][1],
                                "thumbnail": {
                                    "imageUrl": reserve_list[1][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "예매하기",
                                        "webLinkUrl": reserve_list[1][3]
                                    }
                                ]
                            },
                            {
                                "title": reserve_list[2][0],
                                "description": reserve_list[2][1],
                                "thumbnail": {
                                    "imageUrl": reserve_list[2][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "예매하기",
                                        "webLinkUrl": reserve_list[2][3]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


# 취향별 추천
@app.route('/api/preference', methods=['POST'])
def preference():
    body = request.get_json()  # body(SkillPayload)
    print(body)  # SkillPayload 출력
    
    movies_name = body["action"]["detailParams"]["movies_name"]["value"]
    recommendation_list = returnPreference(movies_name)
    
    movie_list = []
    for movieNm in recommendation_list:
        encText = urllib.parse.quote(movieNm)
        url = "https://movie.naver.com/movie/search/result.naver?query=" + encText + "&section=all&ie=utf8"
        html = urllib.request.urlopen(url).read()
        soup = bs(html, 'html.parser')
        img = soup.select_one(".search_list_1 .result_thumb a img")
        link = soup.select_one(".search_list_1 .result_thumb a")
        movie_list.append([movieNm, img["src"], "https://movie.naver.com" + link["href"]])
    
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": movie_list[0][0],
                                "thumbnail": {
                                    "imageUrl": movie_list[0][1]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": movie_list[0][2]
                                    }
                                ]
                            },
                            {
                                "title": movie_list[1][0],
                                "thumbnail": {
                                    "imageUrl": movie_list[1][1]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": movie_list[1][2]
                                    }
                                ]
                            },
                            {
                                "title": movie_list[1][0],
                                "thumbnail": {
                                    "imageUrl": movie_list[1][1]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": movie_list[1][2]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


# 배우별 추천
@app.route("/actor",methods=['POST'])
def actorInput():
    body = request.get_json()  
    print(body)  # SkillPayload 출력
    actor_name = body["action"]["detailParams"]["sys_person_name"]["value"]

    answer = actorMovie(actor_name)
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": answer[0][0],
                                "description": answer[0][3] + ", " + answer[0][4],
                                "thumbnail": {
                                    "imageUrl": answer[0][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[0][1]
                                    }
                                ]
                            },
                            {
                                "title": answer[1][0],
                                "description": answer[1][3] + ", " + answer[1][4],
                                "thumbnail": {
                                    "imageUrl": answer[1][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[1][1]
                                    }
                                ]
                            },
                            {
                                "title": answer[2][0],
                                "description": answer[2][3] + ", " + answer[2][4],
                                "thumbnail": {
                                    "imageUrl": answer[2][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[2][1]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


# 국가별 추천
@app.route("/nation",methods=['POST'])
def nationInput():
    body = request.get_json()  
    print(body)  # SkillPayload 출력
    nation_name = body["action"]["detailParams"]["sys_nation"]["value"]

    answer = nationMovie(nation_name)
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": answer[0][0],
                                "description": answer[0][3] + ", " + answer[0][4],
                                "thumbnail": {
                                    "imageUrl": answer[0][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[0][1]
                                    }
                                ]
                            },
                            {
                                "title": answer[1][0],
                                "description": answer[1][3] + ", " + answer[1][4],
                                "thumbnail": {
                                    "imageUrl": answer[1][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[1][1]
                                    }
                                ]
                            },
                            {
                                "title": answer[2][0],
                                "description": answer[2][3] + ", " + answer[2][4],
                                "thumbnail": {
                                    "imageUrl": answer[2][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": answer[2][1]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)