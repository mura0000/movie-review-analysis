import bs4
from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from urllib.request import urlopen
import datetime
import argparse
import time
import pandas as pd
import os
from datetime import datetime as dt

start = dt.now()

def month_to_num(month):
    num = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4.,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }[month]

    return int(num)

#Create parser
parser = argparse.ArgumentParser(description='Retrieve reviews of a selected movie in IMDb and generate a csv file.')

parser.add_argument("url", help="url of the review list page")

parser.add_argument("--save_dir",
                    dest="save_dir", default="datasets",
                    help="directory for storing the csv file")

parser.add_argument("--filename",
                    dest="filename", default=None,
                    help="name of the csv file to be saved. default set to (movie-title).csv")

args = parser.parse_args()


#Open URL
url = args.url
driver = webdriver.Chrome("./chromedriver")
driver.get(url)

#Get the movie title
bs_title = soup(driver.page_source, "html.parser")
movie_title = bs_title.find("div", {"class": "subpage_title_block__right-column"}).a.text
print("Movie title: {}".format(movie_title))


#Obtain all the divs and get the html source code
while driver.find_element_by_css_selector("button.ipl-load-more__button"):
    try:
        wait = WebDriverWait(driver, 7)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ipl-load-more__button")))
        load_more_button = driver.find_element_by_css_selector("button.ipl-load-more__button")
        load_more_button.click()

    except exceptions.TimeoutException:
        break

review_list_html = driver.page_source
driver.close()



#Get the number of reviews
review_list_page_parser = soup(review_list_html, "html.parser")
review_containers = review_list_page_parser.findAll("div", {"class": "review-container"})
print("Number of reviews: " + str(len(review_containers)))

#Elements to be included in dataframe
stars = []
titles = []
review_dates = []
num_votes = []
num_votes_helpful = []
review_contents = []

#Retrieve reviews and related info
counter = 1
print("Starting to retrieve reviews")
for review in review_containers:
    if counter % 20 == 0:
        print("--Count: {}".format(counter))

    #get brand
    review_loc = review.find("a", {"class": "title"})
    review_url = "https://www.imdb.com" + review_loc["href"]
    uReview = urlopen(review_url)
    page_html = uReview.read()
    uReview.close()

    review_bs = soup(page_html, "html.parser")

    #stars
    try:
        rate = review_bs.find("span", {"class": "rating-other-user-rating"})
        stars.append(float(rate.span.text))
        #print("rate: {}".format(rate.span.text))
    except:
        stars.append(None)

    #titles
    titles.append(review_bs.find("a", {"class": "title"}).text.strip())
    #print("title: {}".format(titles[-1]))

    #review date
    date_str = review_bs.find("span", {"class": "review-date"}).text.split()
    year = int(date_str[2])
    month = month_to_num(date_str[1])
    day = int(date_str[0])
    review_dates.append(datetime.date(year, month, day))
    #print("date: {}".format(review_dates[-1]))

    #vote
    vote = review_bs.find("div", {"class": "actions text-muted"}).text
    vote = vote.strip()
    vote = vote.split()

    num_votes.append(float(vote[3]))
    num_votes_helpful.append(float(vote[0]))

    #print("Number of votes: {}".format(num_votes[-1]))
    #print("Number of voters who said useful: {}".format(num_votes_helpful[-1]))

    #review_contents
    content = review_bs.find("div", {"class": "content"})
    review_contents.append(content.div.text)
    #print("contents: {}".format(review_contents[-1]))
    #print("-----------------------------------")

    counter += 1

print("finished retrieving reviews")


#Create destination for the csv file
if args.filename is None:
    args.filename = "-".join(movie_title.split()) + ".csv"

sv = ""
if args.save_dir is None:
    sv = args.filename
else:
    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)
    sv = args.save_dir + "/" + args.filename

#Create dataframe
reviews_df = pd.DataFrame({
    "star": stars,
    "title": titles,
    "date": review_dates,
    "number_of_votes": num_votes,
    "number_of_votes_helpful": num_votes_helpful,
    "content": review_contents
})

#Save csv file
reviews_df.to_csv(sv)

timeDiff = dt.now() - start
print("Elapsed Time (in Seconds): " + str(timeDiff.seconds))
print("done")
