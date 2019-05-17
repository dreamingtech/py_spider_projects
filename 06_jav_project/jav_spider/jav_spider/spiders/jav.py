# -*- coding: utf-8 -*-
import scrapy
import re


class JavSpider(scrapy.Spider):
    name = 'jav'
    allowed_domains = ['javzoo.com', 'netcdn.space']
    start_urls = ['https://javzoo.com/en']

    def parse(self, response):
        """解析列表页"""
        video_nodes = response.xpath('//div[@id="waterfall"]/div[@class="item"]')
        for video_node in video_nodes:
            video_thumbnail_url = video_node.xpath('.//img/@src').extract_first()
            video_detail_url = video_node.xpath('./a/@href').extract_first()
            meta = {
                "video_thumbnail_url": video_thumbnail_url,
                "video_detail_url": video_detail_url,
            }
            yield scrapy.Request(url=video_detail_url, dont_filter=True, callback=self.parse_detail, meta=meta)
            break

        # 下一页
        next_page_url = response.xpath('//a[@name="nextpage"]/@href').extract_first(default='')
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, dont_filter=True, callback=self.parse)
        pass

    def parse_detail(self, response):

        language = re.match(r'https://javzoo.com/(.*?)/movie.*', response.url).group(1)

        vid_xpath_base = '//span[contains(text(), "{}")]/following-sibling::span/text()'
        release_xpath_base = '//span[contains(text(), "{}")]/following-sibling::text()'
        length_xpath_base = '//span[contains(text(), "{}")]/following-sibling::text()'
        director_xpath_base = '//span[contains(text(), "{}")]/following-sibling::a/text()'
        director_url_xpath_base = '//span[contains(text(), "{}")]/following-sibling::a/@href'
        studio_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/text()'
        studio_url_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/@href'
        publisher_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/text()'
        publisher_url_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/@href'
        series_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/text()'
        series_url_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p[1]/a/@href'
        category_nodes_xpath_base = '//p[contains(text(), "{}")]/following-sibling::p/span/a'

        vid_xpath_signature = {"en": "ID", "cn": "识别码", "tw": "識別碼", "ja": "品番"}
        release_xpath_signature = {"en": "Release Date", "cn": "发行时间", "tw": "發行日期", "ja": "発売日"}
        length_xpath_signature = {"en": "Length", "cn": "长度", "tw": "長度", "ja": "収録時間"}
        director_xpath_signature = {"en": "Director", "cn": "导演", "tw": "導演", "ja": "監督"}
        studio_xpath_signature = {"en": "Studio", "cn": "制作商", "tw": "製作商", "ja": "メーカー"}
        publisher_xpath_signature = {"en": "Label", "cn": "发行商", "tw": "發行商", "ja": "レーベル"}
        series_xpath_signature = {"en": "Series", "cn": "系列", "tw": "系列", "ja": "シリーズ"}
        category_nodes_xpath_signature = {"en": "Genre", "cn": "类别", "tw": "類別", "ja": "ジャンル"}

        vid_xpath = vid_xpath_base.format(vid_xpath_signature.get(language))
        release_xpath = release_xpath_base.format(release_xpath_signature.get(language))
        length_xpath = length_xpath_base.format(length_xpath_signature.get(language))
        director_xpath = director_xpath_base.format(director_xpath_signature.get(language))
        director_url_xpath = director_url_xpath_base.format(director_xpath_signature.get(language))
        studio_xpath = studio_xpath_base.format(studio_xpath_signature.get(language))
        studio_url_xpath = studio_url_xpath_base.format(studio_xpath_signature.get(language))
        publisher_xpath = publisher_xpath_base.format(publisher_xpath_signature.get(language))
        publisher_url_xpath = publisher_url_xpath_base.format(publisher_xpath_signature.get(language))
        series_xpath = series_xpath_base.format(series_xpath_signature.get(language))
        series_url_xpath = series_url_xpath_base.format(series_xpath_signature.get(language))
        category_nodes_xpath = category_nodes_xpath_base.format(category_nodes_xpath_signature.get(language))

        title = response.xpath('//h3/text()').extract_first()
        vid = response.xpath(vid_xpath).extract_first()  # 视频id, 单值
        release = response.xpath(release_xpath).extract_first()  # 发布时间, 单值
        length = response.xpath(length_xpath).extract_first()  # 视频长度, 单值
        length = re.search(r'\d+', length).group()
        director = response.xpath(director_xpath).extract_first(default='')  # 可能不存在, 多值
        director_url = response.xpath(director_url_xpath).extract_first(default='')  # 可能不存在, 单值
        studio = response.xpath(studio_xpath).extract_first(default='')   # 可能不存在, 多值
        studio_url = response.xpath(studio_url_xpath).extract_first(default='')  # 可能不存在, 单值
        publisher = response.xpath(publisher_xpath).extract_first(default='')  # 可能不存在, 多值
        publisher_url = response.xpath(publisher_url_xpath).extract_first(default='')  # 可能不存在, 单值
        series = response.xpath(series_xpath).extract_first(default='')  # 可能不存在, 多值
        series_url = response.xpath(series_url_xpath).extract_first(default='')  # 可能不存在, 单值
        category_nodes = response.xpath(category_nodes_xpath)

        # [{"category_name": "Facial", "category_url":"https://javzoo.com/en/genre/5"}]
        categories = []
        for category_node in category_nodes:
            category_name = category_node.xpath('./text()').extract_first()  # 多值
            category_url = category_node.xpath('./@href').extract_first()  # 单值
            categories.append({"category_name": category_name, "category_url": category_url})
            # break

        # 每种语言对应的字段值可能不同, 定义列表保存字典格式的值
        director_dict = response.meta.get("director_dict", {})
        studio_dict = response.meta.get("studio_dict", {})
        publisher_dict = response.meta.get("publisher_dict", {})
        series_dict = response.meta.get("series_dict", {})
        category_dict = response.meta.get("category_dict", {})

        if director:
            director_dict[language] = director
        if studio:
            studio_dict[language] = studio
        if publisher:
            publisher_dict[language] = publisher
        if series:
            series_dict[language] = series
        if categories:
            # {"en":[{"category_name": "Facial", "category_url": "https://javzoo.com/en/genre/5"}]}
            category_dict[language] = categories

        # 演员, 可能为空
        star_nodes = response.xpath('//div[@id="avatar-waterfall"]/a')
        star_list = []
        for star_node in star_nodes:
            star_name = star_node.xpath('./span/text()').extract_first()
            star_url = star_node.xpath('./@href').extract_first()
            star_pic = star_node.xpath('./div/img/@src').extract_first()
            star_list.append({"star_name": star_name, "star_url": star_url, "star_pic": star_pic})

        # 样品图像, 可能为空
        sample_nodes = response.xpath('//div[@id="sample-waterfall"]/a')
        sample_list = []
        for sample_node in sample_nodes:
            sample_thumbnail_url = sample_node.xpath('./div/img/@src').extract_first()
            sample_pic_url = sample_node.xpath('./@href').extract_first()
            sample_list.append({"sample_thumbnail_url": sample_thumbnail_url, "sample_pic_url": sample_pic_url})

        # 列表页图片
        video_thumbnail_url = response.meta.get("video_thumbnail_url", "")
        # 详情页图片
        big_image = response.xpath('//a[@class="bigImage"]/@href').extract_first()

        meta = {
            "url": response.url,
            "title": title,
            "vid": vid,
            "release": release,
            "length": length,
            "director_dict": director_dict,
            "director_url": director_url,
            "studio_dict": studio_dict,
            "studio_url": studio_url,
            "publisher_dict": publisher_dict,
            "publisher_url": publisher_url,
            "series_dict": series_dict,
            "series_url": series_url,
            "category_dict": category_dict,
            "star_list": star_list,
            "sample_list": sample_list,
            "video_thumbnail_url": video_thumbnail_url,
            "big_image": big_image,
        }

        # if response.meta.get("category_dict", {}):
        if  {"cn", "en", "ja", "tw"} == set(response.meta.get("category_dict", {}).keys()):
            yield meta
            # else:
        for lan in ({"cn", "en", "ja", "tw"} - set(response.meta.get("category_dict", {}).keys())):
            if not lan == language:
                url_sign = re.match(r'https://javzoo.com/.*?/movie/(.*)', response.url).group(1)
                url = "https://javzoo.com/{}/movie/{}".format(lan,url_sign)
                yield scrapy.Request(url=url, callback=self.parse_detail, meta=meta)

        pass