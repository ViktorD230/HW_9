import json
import scrapy
from itemadapter import ItemAdapter
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field

# import  models mongoDB and connect to mongoDB
from models import Authors, Quotes
import connect_to_mongo


# class for defining the structure of quotes elements
class QuoteItem(Item):
    tags = Field()
    author = Field()
    quote = Field()


# class for defining the structure of authors elements
class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


# Scrapy pipeline class for processing received data
class QuotesPipeline:
    qoutes = []
    authors = []

    # method for checking the element type of received data
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if "fullname" in adapter.keys():
            self.authors.append(
                {
                    "fullname": adapter["fullname"],
                    "born_date": adapter["born_date"],
                    "born_location": adapter["born_location"],
                    "description": adapter["description"],
                }
            )

        if "quote" in adapter.keys():
            self.qoutes.append(
                {
                    "tags": adapter["tags"],
                    "author": adapter["author"],
                    "quote": adapter["quote"],
                }
            )

        return item

    # method for saving the received data to files and then writing them to the DB
    def close_spider(self, spider):
        with open("quotes.json", "w", encoding="utf-8") as fd:
            json.dump(self.qoutes, fd, ensure_ascii=False, indent=4)
        with open("authors.json", "w", encoding="utf-8") as fd:
            json.dump(self.authors, fd, ensure_ascii=False, indent=4)

        with open("authors.json", "r", encoding="utf-8") as fa:
            unpackeds = json.load(fa)
            for unpack in unpackeds:
                author = Authors(
                    fullname=unpack.get("fullname"),
                    born_date=unpack.get("born_date"),
                    born_location=unpack.get("born_location"),
                    description=unpack.get("description"),
                ).save()

        with open("quotes.json", "r", encoding="utf-8") as fq:
            unpackeds = json.load(fq)
            for unpack in unpackeds:
                author_name = unpack.get("author")
                author = Authors.objects(fullname=author_name).first()
                quote = Quotes(
                    tags=unpack.get("tags"), author=author, quote=unpack.get("quote")
                ).save()


# Scrapy web spider definition
class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]
    custom_settings = {"ITEM_PIPELINES": {QuotesPipeline: 100}}

    # main page parsing
    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            tags = quote.xpath("div[@class='tags']/a/text()").extract()
            author = quote.xpath("span/small/text()").get()
            q = quote.xpath("span[@class='text']/text()").get()
            yield QuoteItem(tags=tags, author=author, quote=q)
            yield response.follow(
                url=self.start_urls[0] + quote.xpath("span//a/@href").get(),
                callback=self.parse_about_author,
            )

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    # nested page parsing
    def parse_about_author(self, response):
        about = response.xpath("/html//div[@class='author-details']")
        fullname = about.xpath("h3[@class='author-title']/text()").get()
        born_date = about.xpath("p/span[@class='author-born-date']/text()").get()
        born_location = about.xpath(
            "p/span[@class='author-born-location']/text()"
        ).get()
        description = (
            about.xpath("div[@class='author-description']/text()").get().strip()
        )
        yield AuthorItem(
            fullname=fullname,
            born_date=born_date,
            born_location=born_location,
            description=description,
        )


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()
