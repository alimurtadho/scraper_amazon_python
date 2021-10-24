

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, quote_plus
from get_output import get_json, get_csv, get_html
from get_proxies import get_proxies
import argparse

def parse_arguments():
	parser = argparse.ArgumentParser(description='Launch amazon scraper')
	parser.add_argument('-k', '--keyword', required=True, help='Enter your keyword')
	parser.add_argument('-p', action="store_true", help='Enter "-p" to enable proxies')
	parser.add_argument('-j', '--json', action='store_true')
	args = vars(parser.parse_args())
	return get_products(args)

BASE_URL = 'https://www.amazon.com'

headers = {
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
'cache-control': 'max-age=0',
'upgrade-insecure-requests': '1',
'accept-language': 'en-US,en;q=0.9',
'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
}

block_str = 'To discuss automated access to Amazon data please contact api-services-support@amazon.com.'
product_data = []
session = requests.Session()

proxies = None

def get_products_amazon(args):
	page_num = 1

	if args['p']:
		global proxies
		proxies = get_proxies()

	keyword = quote_plus(args['keyword'].strip())

	while True:
		resp = session.get(f'https://www.amazon.com/s?k={keyword}&page={page_num}', proxies=proxies, headers=headers)
		soup = BeautifulSoup(resp.text, 'lxml')
		data = soup.select('div[data-component-type="s-search-result"]')

		for i in data:

			dat = {
			'SOURCE_URL': resp.url,
			'PAGE': page_num,
			'KEYWORD': args['keyword'].strip(),
			'PRODUCT_LINK': ''.join([urljoin(BASE_URL, x.get('href')) for x in i.select('h2 a.a-link-normal.a-text-normal')]),
			'PRODUCT_NAME': ''.join([x.text.strip() for x in i.select('h2 a.a-link-normal.a-text-normal')]),
			'PRICE': ''.join([x.text for x in i.select('span.a-price:nth-of-type(1) span.a-offscreen')]),
			'PRODUCT_RATING': ''.join([x.text[:3] for x in i.select('div.a-row.a-size-small span[aria-label]:nth-of-type(1)')]),
			'NUMBER_OF_RATINGS': ''.join([x.text.strip() for x in i.select('div.a-row.a-size-small span[aria-label]:nth-of-type(2)')])
			}

			product_data.append(dat)

		pagination = soup.select('ul.a-pagination li.a-last')
		print(f'Getting page: {page_num} for keyword {args["keyword"].strip()}', end='\r')
		
		if pagination:
			page_num += 1

		elif not pagination and block_str in str(soup):
			if not args['json']:
				get_csv(args['keyword'].strip(), product_data)
			elif args['json']:
				get_json(args['keyword'].strip(), product_data)

			get_html(soup)
			print('\n')
			print('You\'ve been blocked by amazon. Try using proxies or wait a bit and start over.\n'
			'Check "last_page" folder for HTML output of an error page')
			return
			
		else:
			if not args['json']:
				get_csv(args['keyword'].strip(), product_data)
			elif args['json']:
				get_json(args['keyword'].strip(), product_data)

			print(f'All pages for {args["keyword"].strip()} have been scraped.')
			return product_data


def get_products_ebay(args):
    
    url = 'https://www.ebay.com/sch/i.html?_nkw={0}&_sacat=0'.format(brand)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    failed = False

    # Retries for handling network errors
    for _ in range(5):
        print ("Retrieving %s"%(url))
        response = requests.get(url, headers=headers, verify=False)
        parser = html.fromstring(response.text)
        print ("Parsing page")

        if response.status_code!=200:
            failed = True
            continue
        else:
            failed = False
            break

    if failed:
        return []

    product_listings = parser.xpath('//li[contains(@id,"results-listing")]')
    raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")
    result_count = ''.join(raw_result_count).strip()
    print ("Found {0} for {1}".format(result_count,brand))
    scraped_products = []

    for product in product_listings:
        raw_url = product.xpath('.//a[contains(@class,"item__link")]/@href')
        raw_title = product.xpath('.//h3[contains(@class,"item__title")]//text()')
        raw_product_type = product.xpath('.//h3[contains(@class,"item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
        raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')
        price  = ' '.join(' '.join(raw_price).split())
        title = ' '.join(' '.join(raw_title).split())
        product_type = ''.join(raw_product_type)
        title = title.replace(product_type, '').strip()
        data = {
                    'url':raw_url[0],
                    'title':title,
                    'price':price
        }
        scraped_products.append(data)
    return scraped_products

if __name__ == '__main__':
	parse_arguments()
