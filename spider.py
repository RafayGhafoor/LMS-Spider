import sys
import re
import os
from pathlib import Path, PurePath

import requests
import bs4

session = requests.Session()
domain = 'http://www.kipslms.com'  # domain of the site to be used in subsequent requests.


def scrape_page(url, params='', soup='n', timeout=50):
        '''
        Scrape given link and create a beautiful soup object.

        @args:
        
        url:  URL to be scraped.
        soup: "y" - returns soup object, "n" returns request response.
        '''

        try:
            request_url = session.get(url, params=params, timeout=timeout)

            if request_url.status_code == 401:
                sys.exit("Username or Password is incorrect.")

            elif request_url.status_code == 200:
                if soup == 'y':
                    html_soup = bs4.BeautifulSoup(request_url.content, 'lxml')
                    return html_soup
                return request_url

        except requests.exceptions.ConnectionError:
            raise Exception("Internet Connection Down.\nExiting...")


# TODO: Credentials validity from the server.
def login(username, password, url='http://www.kipslms.com/Account/Login'):
    '''
    Login online portal, takes in username and password of the site
    as an argument.
    '''    
    if not username or not password:
        raise Exception("Username or Password not specified.")

    soup = scrape_page(url=url, soup='y')
    payload = {"UserName": username, "Password": password, "__RequestVerificationToken": soup.find('input').get('value'), 'RememberMe': "true"}
    return session.post(url, data=payload).status_code


def get_course_link(url='http://www.kipslms.com/Candidate/GetMyProgramsPartialView'):
    '''Obtain course link (FUNG | ECAT) from KipsLMS homepage.'''
    soup = scrape_page(url, params={'programType': 2}, soup='y')
    return domain + soup.find('div', class_='programs-list-links').find('a').get('href')


def get_subjects(url='http://www.kipslms.com/Candidate/Course?q=NYwfm4TSzL7uZkBX5aA1tUfMQ3sGz1+S'):
    '''
    Obtain subjects of the session, you're currently enrolled in and their corresponding 
    urls for lectures scraping of a particular subject.

    Example: 
    English > URL
    Physics > URL
    Mathematics > URL

    Return:
    {"English": Subject_URL, "Physics": Subject_URL}
    '''
    subjects_info = {}
    soup = scrape_page(url, soup='y')
    
    for subjects in soup.find('ul', class_="level-2-indent").findAll('a'):
        subjects_info[subjects.text.lower()] = domain + subjects.get('href')

    return subjects_info


def get_subject_weeks(url):
    '''
    Obtain weeks urls whose lectures are/will be available.

    Example: English | http://link.com/Subject

    Week 1 -> Lectures Links....
    Week 2 -> Lectures Links....
    
    Returns: {1: links..., 2: links....}
    '''
    week_track = {}
    # subjects is a dictionary, name is the name of the subject
    soup = scrape_page(url, soup='y')

    class_lst = [ "week-item activity-group-nav-default ",
                  "week-item activity-group-nav-current ", ]
    
    for classes in class_lst:
    
        for subject_info in soup.findAll('li', class_=classes):
            week_info = subject_info.find('span', class_='week-txt').find('a')
            week_info_url, week_num = week_info.get('href'), re.search('\d', week_info.text).group()
            week_track[int(week_num)] = domain + week_info_url
    
    return week_track


def get_videos_links(url):
    '''Obtain videos from the provided webpage along with their names.'''
    soup = scrape_page(url, soup='y')
    # A dictionary containing pair of url of the video and its title.
    return dict([
                (info.text, domain+info.get('href')) for videos in soup.findAll('div', class_='content')\
                                              for info in videos.findAll('a')\
                                              if info.get('href').startswith('/')
                ])


def get_video_page(url):
    '''Obtain video links for downloading of the lecture videos for the topics.'''
    soup = scrape_page(url, soup='y')
    content_id = soup.find('input', attrs={'id': 'hfDetailContentId'}).get('value')
    sos_details_id = soup.find('input', attrs={'id': 'hfSOSDetailId'}).get('value')
    return 'http://www.kipslms.com/Content/GetContentVideoPartialView?contentId={}&sosDetailId={}'.format(content_id, sos_details_id)
    

def get_upstream_link(url):
    '''Returns upstream link of video.'''
    return scrape_page(url, soup='y') .find('source').get('src')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise Exception("Login credentials not provided")
    else:    
        username, password = sys.argv[1], sys.argv[2]
    
    print("Logging into your account....\n")

    if login(username, password) == 200:
        print("Sucessfully Logged in.\n")

    # Obtain physics subjects link from your course home page section i.e., [Physics | Chemistry | Maths]
    subjects_url = get_subjects()
    
    for subject_name, subject_link in subjects_url.items():
        
            Path(subject_name).mkdir(exist_ok=True)
            os.chdir(subject_name)
            subjects_weeks = get_subject_weeks(url=subject_link)
            
            for weeks, url in subjects_weeks.items():
                Path("Week " + str(weeks)).mkdir(exist_ok=True)
                os.chdir("Week " + str(weeks))
                for name, url in get_videos_links(subjects_weeks[weeks]).items():
                    print("Downloading....{}".format(name))           
                    if not Path(name + '.mp4').exists():     
                        try:

                            dl_link = get_upstream_link(get_video_page(url))
                            r = requests.get(dl_link, stream=True)
                            with open(name + '.mp4', 'wb') as f:
                                for chunk in r.iter_content(chunk_size=150):
                                    if chunk:
                                        f.write(chunk)

                        except:
                            print("Some error occured while downloading {}".format(name))
                            continue
                    else:
                        print("{}.mp4 Downloaded".format(name))
                
                os.chdir('..')


            os.chdir('..')
                
