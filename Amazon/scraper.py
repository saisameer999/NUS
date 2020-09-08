from selenium import webdriver
from parsel import Selector

from time import sleep

import pandas as pd


def scroll_to_bottom(x):
    SCROLL_PAUSE_TIME = x

# Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_ratings(temp_sel):
    ratings = ''
    for i in range(1, 6):
        ratings = temp_sel.xpath(f"//i[@class='a-icon a-icon-star-small a-star-small-{i}-5 aok-align-bottom']/span/text()").get()
        try:
            return float(ratings.split()[0])
        except:
            pass
        
        ratings = temp_sel.xpath(f"//i[@class='a-icon a-icon-star-small a-star-small-{i} aok-align-bottom']/span/text()").get()
        try:
            return float(ratings.split()[0])
        except:
            pass


def get_product_df(x):
    df = {'title': [], 'ratings': [], 'num_rated': [], 'dis_price': [], 'act_price': [], 'url': []}
    divs = sel.xpath("//div[@class='a-section a-spacing-medium']").getall()

    for div in divs:
        temp_sel = Selector(text=div)

        sponsored = ''
        try:
            sponsored = temp_sel.xpath("//span[@class='a-size-base a-color-secondary']/text()").get()
        except:
            pass

        if sponsored == 'Sponsored':
            continue

        title = temp_sel.xpath("//span[@class='a-size-medium a-color-base a-text-normal']/text()").get()

        # try for 3 unique classes of ratings

        ratings = get_ratings(temp_sel)

        # get the number of ratings
        try:
            num_rated = int(temp_sel.xpath("//a[@class='a-link-normal']/span[@class='a-size-base']/text()").get().replace(',', ''))
        except:
            num_rated = 0

        # try to get discounted price
        try:
            dis_price = float(temp_sel.xpath("//span[@class='a-price']/span[@class='a-offscreen']/text()").get()[1:])
        except:
            continue

        # if discounted price is not available, skip the data point
        if str(dis_price) == '':
            continue

        try:
            act_price = float(temp_sel.xpath("//span[@class='a-price a-text-price']/span[@class='a-offscreen']/text()").get()[1:])
        except:
            act_price = dis_price

        url = 'https://www.amazon.com' + temp_sel.xpath('//a[@class="a-link-normal a-text-normal"]/@href').get()

        df['title'].append(title)
        df['ratings'].append(ratings)
        df['num_rated'].append(num_rated)

        df['dis_price'].append(dis_price)
        df['act_price'].append(act_price)
        df['url'].append(url)
    return pd.DataFrame(df)


def get_reviews(sel):
    divs = sel.xpath("//div[@class='a-section celwidget']").getall()
    rev_dict = {'ratings': [], 'rev_head': [], 'revs': []}
    for div in divs:
        temp_sel = Selector(text=div)

        ratings = temp_sel.xpath("//i[starts-with(@class,'a-icon a-icon-star a-star-')]/span/text()").get()
        ratings = float(ratings.split()[0])

        heading = temp_sel.xpath("//a[@class='a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold']/span/text()").get()

        rev = temp_sel.xpath("//span[@class='a-size-base review-text review-text-content']/span/text()").get()

        rev_dict['ratings'].append(ratings)
        rev_dict['rev_head'].append(heading)
        rev_dict['revs'].append(rev)

    return pd.DataFrame(rev_dict)

driver = webdriver.Chrome('/home/anudeep/Downloads/cd/chromedriver_linux64/chromedriver')

print("What would you like to shop for today?")
query = input()
query.replace(' ', '+')

driver.get(f'https://www.amazon.com/s?k={query}')
scroll_to_bottom(1)
sel = Selector(text=driver.page_source)

products = sel.xpath("//span[@class='a-size-base-plus a-color-base a-text-normal']/text()").getall()
df = get_product_df(len(products))

for i in range(2, 6):
    driver.get(f'https://www.amazon.com/s?k={query}&page={i}')
    scroll_to_bottom(0.5)
    sel = Selector(text=driver.page_source)

    products = sel.xpath("//span[@class='a-size-base-plus a-color-base a-text-normal']/text()").getall()
    df = pd.concat([df, get_product_df(len(products))])
df = df.reset_index()
df = df.drop('index', axis=1)

rev_dfs = {}
for x in range(df.shape[0]):
    url = df.url[x]
    prod_name = url.split('/')[3]
    asid = url.split('/')[5]

    driver.get(f'https://www.amazon.com/{prod_name}/product-reviews/{asid}?pageNumber=1')
    scroll_to_bottom(0.5)
    sel = Selector(text=driver.page_source)
    rev_df = get_reviews(sel)

    for y in range(2, min(15, df.num_rated[x] // 10)):
        driver.get(f'https://www.amazon.com/{prod_name}/product-reviews/{asid}?pageNumber={y}')
        scroll_to_bottom(0.5)
        sel = Selector(text=driver.page_source)
        rev_df = pd.concat([rev_df, get_reviews(sel)])

    # rev_dfs[x] = rev_df
    rev_df.to_csv(f'reviews/{prod_name}*{asid}*reviews.csv', index=False)
