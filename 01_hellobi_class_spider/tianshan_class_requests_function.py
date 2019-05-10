import requests
import os
import re
import random
import json
from lxml import etree
import time

import logging


# 方法一: 使用logging.basicConfig, 推荐, 只需要调用函数即可, 不需要传递logger
def logging_init():
    # 定义文件处理器f_handler并进行设置
    f_handler = logging.FileHandler('error.log')
    f_handler.setLevel(logging.DEBUG)
    f_handler_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(filename)s[:%(lineno)d] - %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    f_handler.setFormatter(f_handler_formatter)

    # 定义stream handler, stream=None等价于stream=sys.stderr, 等价于不写参数
    s_handler = logging.StreamHandler(stream=None)
    s_handler.setLevel(logging.DEBUG)

    s_handler_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(filename)s[:%(lineno)d] - %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    s_handler.setFormatter(s_handler_formatter)

    # logging.basicConfig中的handlers参数必须是一个可迭代列表
    handler_list = [s_handler, f_handler]

    logging.basicConfig(
        handlers=handler_list,
    )

    logging.getLogger("requests").setLevel(logging.DEBUG)
    requests_log = logging.getLogger("urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def get_response_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
    except ConnectionError as error_msg:
        print('*' * 100)
        print('\t产生错误了:\t%s' % error_msg)
        logging.info('产生错误了%s' % error_msg)
        print('*' * 100)

    html = etree.HTML(response.text)
    return html


# 获取每个课程的分类 定义字典, 三个键为 课程形式, 课程方向, 课程标签. 点击课程形式中的每个分类, 获取所有的课程, 把这些课程的 课程形式改为对应的分类. 同样, 点击课程方向和课程标签中的分类, 给同样的课程添加标签. 
def parse_cate_list(html):
    print("*" * 5, "正在获取分类列表", "*" * 5, sep="\t\t")
    logging.info("正在获取分类列表")

    cate_list = []
    # 以每个大分类进行分组
    main_cate_list = html.xpath('//div[contains(@class, "category-list")]')
    # main_cate_list = xpath('//ul[contains(@class, "list-inline")]')
    for main_cate in main_cate_list:
        main_cate_name = main_cate.xpath('./div/text()')[0].strip().strip("：")
        # print(main_cate_name)

        # 对每个大分类中的小分类进行分组
        sub_cate_list = main_cate.xpath('./ul/li')

        for sub_cate in sub_cate_list:
            sub_cate_dict = {}
            # 提取出每个小分类中的名字和url
            sub_cate_name = sub_cate.xpath('./a/text()')[0]
            sub_cate_url = sub_cate.xpath('./a/@href')[0]

            sub_cate_dict["main_cate_name"] = main_cate_name
            sub_cate_dict["sub_cate_name"] = sub_cate_name
            sub_cate_dict["sub_cate_url"] = sub_cate_url + '&page=1'

            # 去除掉"全部"的分类
            if sub_cate_dict["sub_cate_name"] != "全部":
                cate_list.append(sub_cate_dict)

    return cate_list


# 获取课程的url和分类信息
def parse_course_list(cate_list):
    course_url_dict = {}
    course_id_list = []

    for cate_info in cate_list:
        main_cate_name = cate_info['main_cate_name']
        sub_cate_name = cate_info['sub_cate_name']
        sub_cate_url = cate_info['sub_cate_url']

        print(main_cate_name, sub_cate_name, sep=':\t')

        logging.info("正在获取子分类%s" % sub_cate_url)

        html = get_response_html(sub_cate_url)

        course_item = html.xpath('//ul[@class="course-list"]//div[@class="caption"]')

        for item in course_item:

            # https://edu.hellobi.com/course/280
            course_url = item.xpath('./h3/a/@href')[0]
            course_id = re.findall(r'\d+', course_url)[0]

            if course_id not in course_id_list:
                # 如果课程id没有出现过, 是第一次抓取, 就定义一个以course_id为键的字典, 同时把id添加到id列表中
                course_url_dict[course_id] = {}

                if main_cate_name == '课程形式':
                    course_url_dict[course_id]['course_form'] = sub_cate_name
                elif main_cate_name == '课程方向':
                    course_url_dict[course_id]['course_direction'] = sub_cate_name
                elif main_cate_name == '课程标签':
                    course_url_dict[course_id]['course_tag'] = sub_cate_name

                course_id_list.append(course_id)

            else:
                # 如果课程id已经出现过, 就不是第一次出现这个课程, 就不要定义course_id为键的字典了
                if main_cate_name == '课程形式':
                    course_url_dict[course_id]['course_form'] = sub_cate_name
                elif main_cate_name == '课程方向':
                    course_url_dict[course_id]['course_direction'] = sub_cate_name
                elif main_cate_name == '课程标签':
                    course_url_dict[course_id]['course_tag'] = sub_cate_name

        # 提取下一列的链接
        next_url = html.xpath('//ul[@class="pagination"]/li[last()]/a/@href')
        if next_url:
            # 因为要递归调用自身, 所以必须要构建出与cate_list结构相同的参数, 才能正确调用
            next_cate_list = []
            sub_cate_dict = {}

            sub_cate_dict["main_cate_name"] = main_cate_name
            sub_cate_dict["sub_cate_name"] = sub_cate_name
            sub_cate_dict["sub_cate_url"] = next_url[0]
            next_cate_list.append(sub_cate_dict)

            parse_course_list(next_cate_list)

    return course_url_dict


def parse_course_detail(course_url):

    logging.info("正在解析课程页%s" % course_url)

    course_detail = {}
    html = get_response_html(course_url)

    title = html.xpath("//div[@class='course-info']/h1/text()")

    if title == []:
        print(course_url)
        print("标题为空, 请按回车继续")
    else:
        title = title[0]

    desc = html.xpath("//div[@class='course-des']/p/text()")[0].strip() if html.xpath("//div[@class='course-des']/p/text()") else ''

    # 如果课程是免费的
    price = html.xpath("//span[@class='price-free']/text()")
    if price:
        discount_price = '0'
        origin_price = '0'
        discount_time_left = ''
    else:
        discount_price = html.xpath("//div[@class='course-price']/span/span[1]/text()")[0].strip() if html.xpath("//div[@class='course-price']/span/span[1]/text()") else ''
        origin_price = html.xpath("//div[@class='course-price']/span/span[2]/text()")[0].strip() if html.xpath("//div[@class='course-price']/span/span[2]/text()") else ''
        discount_time_left =re.findall(r'\d+天.*?分钟', html.xpath("//div[@class='course-price']/span/span[3]/text()")[0])[0] if html.xpath("//div[@class='course-price']/span/span[3]/text()") else ''
        
    student_number = re.findall(r'\d+', html.xpath("//div[@class='course-price']/span[@class='course-view']/text()")[0])[0] if html.xpath("//div[@class='course-price']/span[@class='course-view']/text()") else '0'
    teacher = html.xpath("//div[@class='media-body']/a[last()]/text()")[0].strip() if html.xpath("//div[@class='media-body']/a[last()]/text()") else ''
    teacher_href = html.xpath("//div[@class='media-body']/a[last()]/@href")[0].strip() if html.xpath("//div[@class='media-body']/a[last()]/@href") else ''
    lesson_num = re.findall(r'\d+', html.xpath("//ul[@role='tablist']/li[2]/a/small/text()")[0])[0] if html.xpath("//ul[@role='tablist']/li[2]/a/small/text()") else ''

    course_detail['title'] = title
    course_detail['desc'] = desc
    course_detail['discount_price'] = discount_price
    course_detail['origin_price'] = origin_price
    course_detail['discount_time_left'] = discount_time_left
    course_detail['student_number'] = student_number
    course_detail['teacher'] = teacher
    course_detail['teacher_href'] = teacher_href
    course_detail['lesson_num'] = lesson_num
    course_detail['url'] = course_url

    return course_detail


def main():
    # 初始化logging, 记录日志
    logging_init()
    # 起始页
    start_url = 'https://edu.hellobi.com/course/explore'

    # 获取首页的响应
    html = get_response_html(start_url)

    # 获取分类和对应的url
    cate_list = parse_cate_list(html)

    # {'280': {'course_form': '付费课程', 'course_direction': 'Python', 'course_tag': 'Python'}, '279': {'course_form': '免费课程', 'course_direction': '数据可视化', 'course_tag': '数据可视化'}, '266': {'course_form': '免费课程', 'course_direction': 'Python', 'course_tag': '机器学习'}, ...}
    course_url_dict = parse_course_list(cate_list)

    course_detail_list = []

    for course_id, course_cate in course_url_dict.items():
        course_url = 'https://edu.hellobi.com/course/' + course_id
        course_detail = parse_course_detail(course_url)
        course_detail_list.append(course_detail)

    print(course_detail_list)


if __name__ == '__main__':
    main()
