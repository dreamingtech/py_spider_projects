import os
import re
import win32api
import win32con
import win32gui

import time
import random
from datetime import datetime

import pymysql

import requests
from requests.auth import HTTPBasicAuth
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver():

    options = webdriver.ChromeOptions()
    # 不显示图片
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--proxy-server=socks5://127.0.0.1:1080")

    # 最大化窗口
    options.add_argument("start-maximized")

    # options.set_headless(headless=True)
    # 添加xpath插件
    # extension_path = r"D:/python_packages/xpath_extension_2_0_2_0.crx"
    # options.add_extension(extension_path)

    driver = webdriver.Chrome(chrome_options = options)

    return driver


# 从首页中解析所有的列表页
def parse_cate_pages(driver, url):
    # 这里不使用点击下一页的方式进行翻页, 因为下一页要解决等待的问题, 直接使用get就不会出现等待的问题
    driver.get(url)

    # 有时候会跳转到这个网址, http://members.sciexp.com/index.php?mode=video, 所以这里进行判断并重试
    for i in range(3):
        if driver.current_url != url:
            print("响应地址不符, 重试中")
            driver.get(url)
            if i == 2:
                print("无法正确获取响应, 请检查")
                break
        else:
            print("正确获得响应, 开始提取信息")
            break

    print("解析当前分类中的所有列表页")
    html = etree.HTML(driver.page_source)
    page_url_list = html.xpath('//nav[@aria-label="pagination-top"]//div[contains(@class,"dropdown-menu")]/a/@href')
    return page_url_list

def deal_time(update_date):
    print("处理更新时间")
    pattern = re.compile(r'(\w+)\s(\d{1,2})\w{2},\s(\d{4})')
    result = pattern.match(update_date)
    update_date = '{} {} {}'.format(result.group(1),result.group(2),result.group(3))
    # 转换为字符串
    update_date = datetime.strptime(update_date, '%B %d %Y').strftime('%Y%m%d')
    return update_date

def get_video_length(download_url):

    print("正在获取视频长度\t%s"%download_url)

    headers = {
        'Referer': 'http://members.sciexp.com/video/12-order/page1.html',
        'Host': 'members.sciexp.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
        'Authorization': 'Basic dmlpaXBsYXlib3k6czZ1OXA1ZTNyOA==',
        'Upgrade-Insecure-Requests': '1',
    }

    # 使用with request.get as response, 就会自动关闭连接
    with requests.get(download_url, stream=True, auth=HTTPBasicAuth('johnhelen14', 'ejis@1824924'), headers=headers) as response:
        video_length = response.headers.get('Content-Length')

    print("获取的视频长度为\t%s"%video_length)

    return video_length

def parse_video_divs(driver, url):
    print("从列表页中提取视频块信息")

    driver.get(url)

    # 有时候会跳转到这个网址, http://members.sciexp.com/index.php?mode=video, 所以这里进行判断并重试
    for i in range(3):
        if driver.current_url != url:
            print("响应地址不符, 重试中")
            print(driver.current_url)
            print(url)
            driver.get(url)
            if i == 2:
                print("无法正确获取响应, 请检查")
                break
        else:
            print("正确获得响应, 开始提取信息")
            break

    # 把每一页提取到的信息保存到一个列表中
    item_list = []
    html = etree.HTML(driver.page_source)

    video_divs = driver.find_elements_by_xpath('//div[@class="update-wrap"]')
    return video_divs   

def parse_video_info(video_div):

    print("开始提取视频信息")

    video_title = video_div.find_element_by_xpath("./div[@class='vidtitle']/p[1]").text 
    update_date = video_div.find_element_by_xpath("./div[@class='vidtitle']/p[2]").text 
    update_date = deal_time(update_date)
    play_address = video_div.find_element_by_xpath(".//div[@class='vidthumb']/a").get_attribute("href")  
    video_id = re.findall(r'\d+', play_address)[0]
    thumb_url = video_div.find_element_by_xpath(".//div[@class='vidthumb']/a/img").get_attribute("src")  
    download_url = video_div.find_element_by_xpath(".//div[@class='controls']//div[@class='barinside']/a").get_attribute("href")  
    video_desc = video_div.find_element_by_xpath(".//div[@class='collapse']/p").text
    video_name = re.split(r'/', download_url)[-1]

    video_info = {
        "video_title": video_title,
        "update_date": update_date,
        "play_address": play_address,
        "thumb_url": thumb_url,
        "download_url": download_url,
        "video_desc": video_desc,
        "video_name": video_name,
        "video_id": video_id,
    }

    print("信息已提取@视频\t%s"%video_id)

    return video_info

# 下载视频, 下载视频的功能应该与提取信息的功能放在一起
def download_video(driver,video_div,video_info):

    download_url = video_info.get('download_url')
    video_file_path = video_info.get('file_path') + '.mp4'

    print("开始下载视频\t%s"%download_url)


    if os.path.exists(video_file_path):
        print("文件已经存在, 跳过")
        return

    dl_icon = video_div.find_element_by_xpath('.//img[@class="dl-icon"]')

    # 使用win32gui查找浏览器窗口
    chrome_window = win32gui.FindWindow("Chrome_WidgetWin_1", driver.title+" - Google Chrome")

    # 把浏览器窗口提到最前, 并设置焦点到浏览器窗口, 否则, 键盘输入的k值不会打开保存文件的对话框, 而是输入到终端窗口.
    # win32gui.BringWindowToTop(chrome_window)
    # 设置浏览器窗口获取焦点
    win32gui.SetForegroundWindow(chrome_window)
    # 激活窗口并使其最大化
    # win32gui.ShowWindow(chrome_window, 8)

    actionchains = ActionChains(driver)
    # 鼠标移动到要操作的元素的位置
    actionchains.context_click(dl_icon).perform()
    #延时2s
    time.sleep(1)

    #按下K键,这里用到了win32api,win32con, 75的含义就是键盘的K
    win32api.keybd_event(75,win32con.KEYEVENTF_KEYUP,0)

    print("="*30)
    print(video_file_path)
    print("="*30)

    time.sleep(1)
    os.system("{} {}".format("D:\\David\\Desktop\\sicdownload_cn.exe", video_file_path))


def gen_file_path(video_info):
    print("生成文件保存位置")
    # 'http://members.sciexp.com/members/sd_content/videos/673/physics001.mp4'
    # 更新时间
    update_date = video_info.get('update_date')
    video_id = video_info.get('video_id')
    # 视频标题
    video_title = video_info.get('video_title')
    video_title = re.sub(r'\W+', '_', video_title)    
    # 视频名称
    download_url = video_info.get('download_url')
    video_name = re.split(r'/', download_url)[-1]
    # 拼接为文件名
    video_file_name = '{}_{}_{}_{}'.format(update_date, video_id, video_title, video_name)

    # 把文件存在在更新年份的文件夹中
    update_year = re.match(r'\d{4}', update_date).group() if re.match(r'\d{4}', update_date) else '0000'
    folder_path = "D:\\sciexp\\" + update_year

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    else:
        print('文件夹已经存在\t%s'%folder_path)

    file_path = folder_path + "\\" + video_file_name

    print("生成的文件路径为\t%s"%file_path)

    # 提取出不包含扩展名在内的文件名
    return file_path[:-4]

def write_txt(video_info):

    txt_file_path = video_info.get('file_path') + '.txt'
    print("写入text文件\t%s"%txt_file_path)

    if os.path.exists(txt_file_path):
        print("文件已经存在, 跳过")
        return

    with open(txt_file_path, 'w', encoding='utf-8', newline="") as f:
        txt_video_info = {
            "Video_title": " " + video_info.get('video_title'),
            "Update_time": " " + video_info.get('update_date'),
            "Video_description": " " + video_info.get('video_desc'),
            "Video_tags": " " + video_info.get('video_tags'),
            "File_path": " " + txt_file_path[:-4]
        }
        for i,j in txt_video_info.items():
            # windows中使用\r\n换行, linux中使用\n换行
            content = "{}:{}\r\n".format(i,j)
            f.write(content)

def download_image(video_info):

    thumb_url = video_info.get('thumb_url')

    print("下载图片\t%s"%thumb_url)
    image_file_path = video_info.get('file_path') + '.jpg'

    if os.path.exists(image_file_path):
        print("文件已经存在, 跳过")
        return

    headers = {
        'Host': 'images.sciexp.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
        'Upgrade-Insecure-Requests': '1',
    }

    response = requests.get(thumb_url, headers=headers)

    with open(image_file_path, 'wb') as f:
        f.write(response.content)

def get_video_tags(driver, play_address):

    print("获取视频标签\t%s"%play_address)

    # video_tags要打开一个新的页面来获取
    driver.execute_script("window.open('" + play_address + "')")
    # 切换到这个新的页面中
    driver.switch_to_window(driver.window_handles[1])

    for i in range(3):
        if driver.current_url != play_address:
            print("响应地址不符, 重试中")
            driver.get(play_address)
            if i == 2:
                print("无法正确获取响应, 请检查")
                break
        else:
            print("正确获得响应, 开始提取信息")
            break

    try:
        # print("====开始等待====")
        element = WebDriverWait(driver, 10, 2).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="vidwrap"]/p[2]/a'))
        )
        # print("====结束等待====")

        html = etree.HTML(driver.page_source)

        tag_list = html.xpath('//div[@class="vidwrap"]/p[2]/a/text()')
        # 把video_tags转换为字符串
        video_tags = ','.join([tag.replace('#','') for tag in tag_list])

    except Exception as e:
        print("====未找标签内容, 请检查====")
        print(e)
        video_tags = ''

    driver.close()
    driver.switch_to_window(driver.window_handles[0])
    print("获取的视频标签为%s"%video_tags)

    return video_tags

def write_to_mysql(video_info):

    print("写入到mysql数据库")

    conn = pymysql.connect(
        host='sh.sql.tencentcdb.com', 
        user='root', 
        password='password', 
        database='sciexp', 
        port=6379,
        )

    cursor = conn.cursor()

    # 通过变量把字段的值插入到数据库中.
    # 因为设置了数据库的id是自动增长的, 插入数据时如果把id设置为null, id会自动在前一条数据的基础上加1
    sql = """
    insert ignore into video_info(id, video_title, update_date, play_address, video_id, thumb_url, download_url, video_desc, video_name, file_path, video_tags) values(null, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (video_info['video_title'], video_info['update_date'], video_info['play_address'], video_info['video_id'], video_info['thumb_url'], video_info['download_url'], video_info['video_desc'], video_info['video_name'], video_info['file_path'], video_info['video_tags']))
    conn.commit()

    conn.close()


def check_video_exists(video_id):
    # 从mysql数据库中检查数据是否存在, 如果数据存在, 就说明已经下载视频, 就可以跳过了.
    print("检查视频是否存在\t%s"%video_id)

    conn = pymysql.connect(
        host='sql.tencentcdb.com', 
        user='root', 
        password='password', 
        database='sciexp', 
        port=6379,
        )

    cursor = conn.cursor()

    sql = "select 1 from video_info where video_id = " + video_id + " limit 1";
    
    video_exists_flag = cursor.execute(sql)

    print(video_exists_flag)

    conn.close()

    return video_exists_flag

def check_video_tags_exists(video_id):
    # 从mysql数据库中检查数据是否存在, 如果数据存在, 就说明已经下载视频, 就可以跳过了.
    print("检查视频标签是否存在\t%s"%video_id)

    conn = pymysql.connect(
        host='sql.tencentcdb.com', 
        user='root', 
        password='password', 
        database='sciexp', 
        port=6379,
        )

    cursor = conn.cursor()

    sql = "select video_tags from video_info where video_id = " + video_id + " limit 1";

    cursor.execute(sql)

    video_tags = cursor.fetchone()

    conn.close()

    return video_tags


def main():
    driver = get_driver()
    # login_url = 'http://johnhelen14:ejis@1824924@members.sciexp.com/'
    # 从任意页获取所有列表页的url地址
    start_url = 'http://johnhelen14:ejis@1824924@members.sciexp.com/video/12-order/page1.html'
    page_url_list = parse_cate_pages(driver, start_url)
    print(page_url_list)

    # 对每一页的url地址发送请求获取其信息
    for page_url in page_url_list:
        print(page_url)
        video_divs = parse_video_divs(driver, page_url)

        for video_div in video_divs:
            # 提取视频信息
            video_info = parse_video_info(video_div)

            # 从mysql数据库中查询数据是否已经存在, 如果已存在, 就跳过
            video_id = video_info.get('video_id')
            video_exists_flag = check_video_exists(video_id)

            # 根据视频id检测视频是否已经下载
            if video_exists_flag == 1:
                print("视频\t%s\t信息已存在"%video_id)
                continue

            # 生成文件保存路径
            file_path = gen_file_path(video_info)
            # 把file_path也保存到video_info中, 方便下载图片和视频时设置路径
            video_info['file_path'] = file_path

            # 下载视频
            download_video(driver,video_div,video_info)

            file_path = video_info.get('file_path') + '.mp4'

            print("检测视频是否已经下载")
            for i in range(1000):

                if os.path.exists(file_path):
                    print("视频已经下载, 继续执行代码")
                    break
                if i >= 30:
                    print("===出现问题, 请检查===")
                    break
                else:
                    print("===视频未下载完成, 继续等待===")
                    time.sleep(30)

            # 下载缩略图
            download_image(video_info)

            # 获取视频长度
            # download_url = video_info.get('download_url')
            # video_length = get_video_length(download_url)
            # video_info['video_length'] = video_length

            # 进入详情页, 获取视频标签
            play_address = video_info.get('play_address')
            video_tags = get_video_tags(driver, play_address)
            video_info['video_tags'] = video_tags
            # 把视频信息写入到mysql数据库中
            write_to_mysql(video_info)
            # 把视频信息写入到txt文件中
            write_txt(video_info)

            time.sleep(random.randint(15,30))

            # break
        # break


if __name__ == '__main__':
    main()
