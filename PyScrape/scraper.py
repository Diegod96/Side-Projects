import requests
from bs4 import BeautifulSoup
from datetime import timedelta
import re
import csv


class EbayScraper(object):
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html?_nkw="
        self.item = self.getItem()
        self.buying_type = self.getBuyingType()
        self.url_seperator = "&_sop=12&rt=nc&LH_"
        self.url_seperator2 = "&_pgn="
        self.currentPage = 1

    # Get user's item
    @staticmethod
    def getItem():
        item = input("Item: ")
        return item

    # Get user's buying type
    # Verify that it is either "Buy It Now" or "Auction"
    @staticmethod
    def getBuyingType():
        buying_type = input("Please specify a buying type (Auction or Buy It Now): ")
        buying_type = buying_type.lower()

        if buying_type == "auction":
            return buying_type
        elif buying_type == "buy it now":
            return buying_type
        else:
            print("Invalid buying type specified.")

    # Get and create URL based off users item and buying type specified
    def getUrl(self, page=1):
        if self.buying_type == "buy it now":
            self.buying_type = "BIN=1"
        elif self.buying_type == "auction":
            self.buying_type = "Auction=1"

        self.item = self.item.replace(" ", "+")
        # _ipg=200 means that expect a 200 items per page
        url = '{}{}{}{}{}{}&_ipg=200'.format(
            self.base_url, self.item, self.url_seperator, self.buying_type,
            self.url_seperator2, page
        )
        request = requests.get(url)
        if request.status_code == 200:
            return url
        else:
            print("Could not connect to Ebay.com")

    # Check if there is next page
    @staticmethod
    def pageHasNext(soup):
        container = soup.find('ol', 'x-pagination__ol')
        if container is None:
            return False
        currentPage = container.find('li', 'x-pagination__li--selected')
        next_sibling = currentPage.next_sibling
        if next_sibling is None:
            print(container)
        return next_sibling is not None

    def iteratePage(self):
        titles = []
        prices = []
        links = []
        conditions = []
        closing_dates = []
        seconds_left = []
        ratings = []

        # This will loop if there are more pages otherwise end
        # Append results from the page to their given list
        while True:
            page = instance.getPageUrl(self.currentPage)
            titles.append(instance.getInfo(page)[0])
            prices.append(instance.getInfo(page)[1])
            links.append(instance.getInfo(page)[2])
            conditions.append(instance.getInfo(page)[3])
            closing_dates.append(instance.getInfo(page)[4])
            seconds_left.append(instance.getInfo(page)[5])
            ratings.append(instance.getInfo(page)[6])
            if self.pageHasNext(page) is False:
                break
            else:
                self.currentPage += 1

        return titles, prices, links, conditions, closing_dates, seconds_left, ratings

    def getPageUrl(self, pageNum):
        url = self.getUrl(pageNum)
        print(f"page #{pageNum}:", url)
        print("\n")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    @staticmethod
    def getInfo(soup):
        titles = []
        prices = []
        links = []
        conditions = []
        closing_dates = []
        seconds_left = []
        ratings = []

        # Iterate through all listings on the current page
        for listing in soup.find_all("li", {"class": "s-item"}):
            raw = listing.find_all("a", {"class": "s-item__link"})

            # First element 0 returns an empty element
            if raw:
                raw_price = listing.find_all("span", {"class": "s-item__price"})[0]
                raw_title = listing.find_all("h3", {"class": "s-item__title"})[0]
                raw_link = listing.find_all("a", {"class": "s-item__link"})[0]
                raw_condition = listing.find_all("span", {"class": "SECONDARY_INFO"})[0]

                # Assign text of element to variables
                condition = raw_condition.text
                title = raw_title.text
                link = raw_link['href']

                # Append variables to their associated list
                titles.append(title)
                conditions.append(condition)
                links.append(link)

                # Some "Buy It Now" listings have an end date, but a majority do not
                # If there is an end date for the current listing we are looking at then get it
                # Else fill the time_left variable with "NONE"
                # If there is not a time to convert to seconds, set seconds to a time that will never be reached by Ebay's standards
                if listing.find_all("span", {"class": "s-item__time-left"}):
                    raw_time_left = listing.find_all("span", {"class": "s-item__time-left"})[0]
                    time_left = raw_time_left.text[:-5]
                    seconds = instance.timeToSeconds(time_left)
                    closing_dates.append(time_left)
                    seconds_left.append(seconds)
                else:
                    time_left = "None"
                    seconds = 10000000
                    closing_dates.append(time_left)
                    seconds_left.append(seconds)

                if listing.find_all("span", {"class": "s-item__etrs-text"}):
                    raw_rating = listing.find_all("span", {"class": "s-item__etrs-text"})[0]
                    rating = raw_rating.text
                    if rating == "Top Rated Plus":
                        ratings.append("YES")
                else:
                    ratings.append("NO")

                # If the price has a comma (i.e, $1,000) then strip comma, get rid of $, and convert to float
                # Else convert to float and get rid of $
                # If a listing has a "$589.00 to $1,200" pricing structure
                # Then split on the "to" and get the average of the two prices and set for price
                raw_price_text = raw_price.text
                if raw_price_text.find("to") != -1:
                    if raw_price_text.find(',') != -1:
                        raw_price_text = raw_price_text.replace(",", "")
                    split = raw_price_text.split(" ")
                    del split[1]
                    price1 = split[0]
                    price2 = split[-1]
                    price1 = float(price1[1:])
                    price2 = float(price2[1:])
                    avg_price = (price1 + price2) / 2
                    avg_price = round(avg_price, 2)
                    prices.append(avg_price)
                elif raw_price_text.find(',') != -1:
                    raw_price_text = raw_price_text.replace(",", "")
                    price = float(raw_price_text[1:])
                    prices.append(price)
                elif raw_price_text.find("to") != -1:
                    split = raw_price_text.split(" ")
                    del split[1]
                    price1 = split[0]
                    price2 = split[-1]
                    price1 = float(price1[1:])
                    price2 = float(price2[1:])
                    avg_price = (price1 + price2) / 2
                    avg_price = round(avg_price, 2)
                    prices.append(avg_price)
                else:
                    price = float(raw_price_text[1:])
                    prices.append(price)

        # Return data to the page iteration function above
        return titles, closing_dates, conditions, prices, links, seconds_left, ratings

    @staticmethod
    def organizeResults(results):
        # Extract specific lists of lists to their appropriate category
        list_of_titles = results[0]
        list_of_closing_dates = results[1]
        list_of_conditions = results[2]
        list_of_prices = results[3]
        list_of_links = results[4]
        list_of_seconds_left = results[5]
        list_of_ratings = results[6]

        # Break down and combine specific list of lists into one list
        titles = []
        for sublist in list_of_titles:
            for title in sublist:
                titles.append(title)
        closing_dates = []
        for sublist in list_of_closing_dates:
            for date in sublist:
                closing_dates.append(date)
        conditions = []
        for sublist in list_of_conditions:
            for condition in sublist:
                conditions.append(condition)
        prices = []
        for sublist in list_of_prices:
            for price in sublist:
                prices.append(price)
        links = []
        for sublist in list_of_links:
            for link in sublist:
                links.append(link)
        seconds = []
        for sublist in list_of_seconds_left:
            for time in sublist:
                seconds.append(time)

        ratings = []
        for sublist in list_of_ratings:
            for rating in sublist:
                ratings.append(rating)

        # Zip lists back up to be returned as a zipped list
        zippedList = list(zip(titles, closing_dates, seconds, conditions, prices, links, ratings))

        return zippedList

    # Convert "xd xh xm xs" to seconds conversion
    @staticmethod
    def timeToSeconds(time):
        UNITS = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
        return int(timedelta(**{
            UNITS.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
            for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhd]?)', time, flags=re.I)
        }).total_seconds())

    # Convert data frame to .csv file
    @staticmethod
    def toCsv(zippedList):
        file = "data.csv"
        with open(file, "w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output, lineterminator='\n')
            for line in zippedList:
                title = line[0]
                closing_dates = line[1]
                seconds = line[2]
                conditions = line[3]
                prices = line[4]
                links = line[5]
                ratings = line[6]
                writer.writerow([title, closing_dates, seconds, conditions, prices, links, ratings])



if __name__ == '__main__':
    instance = EbayScraper()
    results = instance.iteratePage()
    zippedList = instance.organizeResults(results)
    instance.toCsv(zippedList)
