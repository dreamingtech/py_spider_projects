import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re


def get_soup(url):
    headers = {
        'Host': 'book.douban.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
        'Referer': 'https://book.douban.com/tag/?view=type'
    }
    sess = requests.Session()
    response = sess.request('GET',url,headers=headers,allow_redirects=False)
    # response = requests.get(url, headers=headers)
    # response = sess.get(url, headers=headers)

    time.sleep(random.random() * 2)

    soup = BeautifulSoup(response.text, 'lxml')
    return soup


# 获取主分类和次分类
def get_category_dict(url):
    soup = get_soup(url)
    print("*****获取主分类和次分类*****")
    category_dict = {}

    # 获取所有主分类main_category, 得到所有主分类的列表
    main_category = soup.select('a[class="tag-title-wrapper"]')
    # 对每一个主分类, 获取它下面的次分类
    for item in main_category:
        # 主分类的名字
        main_category_name = item.text.replace("·", "").strip()
        # 通过主分类的父标签查找所有子分类
        sub_category_url_list = item.parent.select('a[href]')
        # 使用列表生成式获取所有子分类的url
        sub_category_list = ["https://book.douban.com" + i.get('href') for i in sub_category_url_list]

        # 把主分类和与之对应的次分类url保存到以主分类为名的字典中
        category_dict[main_category_name] = sub_category_list

    return category_dict


# 获取每个子分类下的图书列表
def get_sub_category_book_info(url):
    # 从子分类的url获取子分类的名称

    sub_category_book_info = []

    # 从url获取当前子分类的页数, 如果url中没有包含页码, 就设置为1
    page = re.match(r'.*start=(\d+)', url).group(1) if re.match(r'.*start=(\d+)', url) else 1
    page = round((int(page)/20+1))

    # 测试代码, 只获取前5页的图书信息
    if int(page) > 2:
        return sub_category_book_info

    soup = get_soup(url)
    # 对每一页的内容进行判断, 如果能取到subject-item的li标签, 才进行进一步的操作, 如果没有获取到, 就直接返回sub_category_book_info
    if soup.select('li[class="subject-item"]'):
        # 获取图书的节点
        book_info = soup.select('li[class="subject-item"]')

        print('获取第\t{}\t页的图书列表'.format(page))
        for item in book_info:
            book_name = item.select('div[class="info"] h2 a')[0].get('title') if item.select('div[class="info"] h2 a') else ''
            book_url = item.select('div[class="info"] h2 a')[0].get('href') if item.select('div[class="info"] h2 a') else ''
            book_pic_url = item.select('div[class="pic"] img')[0].get('src') if item.select('div[class="pic"] img') else ''
            book_rating_nums = item.select('span[class="rating_nums"]')[0].text if item.select('span[class="rating_nums"]') else ''
            book_rating_people = re.match(r'.*?(\d+)',item.select('div[class="star clearfix"] span[class="pl"]')[0].text.strip()).group(1) if item.select('span[class="rating_nums"]') else ''
            book_intro = item.select('div[class="info"] p')[0].text if item.select('div[class="info"] p') else ''

            # 把每一个图书的信息保存在一个字典中
            book_info_dict = {}
            book_info_dict['book_name'] = book_name
            book_info_dict['book_url'] = book_url
            book_info_dict['book_pic_url'] = book_pic_url
            book_info_dict['book_rating_nums'] = book_rating_nums
            book_info_dict['book_rating_people'] = book_rating_people
            book_info_dict['book_intro'] = book_intro

            # 格式: {次分类:{图书名:{book_name:xxx, book_url:xxx, book_pic_url:xxx}}}
            sub_category_book_info.append(book_info_dict)

        next_link = soup.select('span[class="next"] link')

        # 如果存在下一页, 就递归调用get_sub_category_book_info获取图书信息, 如果不存在下一页, 就直接返回book_info_list
        if next_link:
            next_link_url = "https://book.douban.com" + next_link[0].get('href')
            get_sub_category_book_info(next_link_url)

    return sub_category_book_info


def write_json(name, data):
    with open("{}.json".format(name), "w", encoding="utf-8") as f:
        # ensure_ascii=False, 如果是中文, 就不转换为ascii, 而是显示为中文. indent在上一级的基础上都缩进2个空格
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def run():
    # 1. 从起始url获取主分类和次分类
    start_url = 'https://book.douban.com/tag/?view=type'
    category_dict = get_category_dict(start_url)
    # 把主次分类信息写入到json文件中
    write_json('category', category_dict)

    # 2. 获取每个次分类下图书的url, category_dict格式: {主分类:[次分类]}
    for main_category_name, sub_category_list in category_dict.items():

        # 主分类下的所有图书信息以字典格式保存 主分类:次分类:图书名:图书信息
        main_category_book_info_dict = {main_category_name: {}}
        # mysql数据库中, 数据库图书信息, 表1, 主分类和次分类1对多, 表2: 次分类和图书1对多, 表3: 图书信息, 书名, 图书url, 作者,出版社,原作名,译者,出版年,页数,定价,装帧,丛书,ISBN,简介

        print("获取\t{}\t主分类下的图书列表".format(main_category_name))

        # 获取每个次分类下图书列表信息
        # for sub_category_url in sub_category_list:
        # 测试代码, 对每个主分类下只获取最后5个子分类的连图书信息
        for sub_category_url in sub_category_list[0:5]:
            sub_category_name = re.match(r'https://book.douban.com/tag/(.*)$', sub_category_url).group(1)
            print('获取\t{}\t次分类下的图书列表'.format(sub_category_name))

        # 一个次分类下所有的图书信息为字典格式
            sub_category_book_info = get_sub_category_book_info(sub_category_url)

            # 把一个次分类下所有的图书信息保存到主分类图书信息的字典中
            main_category_book_info_dict[main_category_name][sub_category_name] = sub_category_book_info

        print("主分类\t{}\t下的图书列表获取成功".format(main_category_name))

        write_json(main_category_name, main_category_book_info_dict)


if __name__ == '__main__':
    run()