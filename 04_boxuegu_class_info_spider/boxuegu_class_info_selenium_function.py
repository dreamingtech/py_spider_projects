import re
import time

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver(username):

    options = webdriver.ChromeOptions()
    # 不显示图片, 在需要关闭促销信息的时候, 必须要显示图片, 否则无法加载出关闭的按钮.
    # 在使用微博登录的时候要输入验证码, 必须要显示图片
    if username.startswith("152"):
        prefs = {
            "profile.managed_default_content_settings.images": 2,
        }
        options.add_experimental_option("prefs", prefs)

    # options.add_argument("--proxy-server=socks5://127.0.0.1:1080")
    # 最大化窗口
    options.add_argument("start-maximized")

    # options.set_headless(headless=True)
    # 添加xpath插件
    extension_path = r"D:/python_packages/XPath-Helper_v2.0.2.crx"
    options.add_extension(extension_path)

    chrome_driver_path = r"D:\python_packages\chromedriver_win32_73.0.3683.68\chromedriver.exe"
    driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options = options)

    return driver


def open_page(driver, url):
    # 这里不使用点击下一页的方式进行翻页, 因为下一页要解决等待的问题, 直接使用get就不会出现等待的问题
    driver.get(url)

    # 根据不同的url选择不同的等待方式
    if url.startswith("https://www.boxuegu.com"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "my-class")
                                                ))
    elif url.startswith("https://xuexi.boxuegu.com/class_track.html"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "StageModuleName")
                                                ))
    elif url.startswith("https://xuexi.boxuegu.com/video.html"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "video_list_warp")
                                                ))

def login_boxuegu(driver, username, password):
    """使用博学谷账号登录"""
    login_button = driver.find_element_by_id("login-button")
    login_button.click()
    time.sleep(2)
    username_input = driver.find_element_by_xpath('//input[@class="cyinput1 form-control userName"]')
    username_input.send_keys(username)
    time.sleep(1)

    password_input = driver.find_element_by_xpath('//input[@class="cyinput2 form-control password"]')
    password_input.send_keys(password)
    time.sleep(1)

    driver.find_element_by_xpath('//button[@class="cymyloginbutton goLogin"]').click()


def weibo_login_boxuegu(driver, username, password):
    """使用微博账号登录"""

    # # 关闭促销信息
    # driver.find_element_by_xpath('//img[@class="february-close"]').click()
    # time.sleep(2)

    login_button = driver.find_element_by_id("login-button")
    login_button.click()
    time.sleep(1)

    weibo_login_button = driver.find_element_by_xpath('//div[@class="weibo-login"]')
    weibo_login_button.click()
    time.sleep(1)

    username_input = driver.find_element_by_id("userId")
    username_input.send_keys(username)

    time.sleep(1)

    password_input = driver.find_element_by_id("passwd")
    password_input.send_keys(password)
    time.sleep(1)

    # 手动输入验证码
    captcha_input = driver.find_element_by_xpath('//input[@class="WB_iptxt oauth_form_input oauth_form_code"]')
    captcha = input("请输入验证码: ")
    captcha_input.send_keys(captcha)

    driver.find_element_by_xpath('//a[@class="WB_btn_login formbtn_01"]').click()

def parse_course_name_url(driver):
    course_name_urls = []
    time.sleep(1)
    html = etree.HTML(driver.page_source)
    # 对每一个课程进行分组
    course_divs = html.xpath('//div[@class="courseWarp"]')
    for course in course_divs:
        course_name = course.xpath('./@data-coursename')[0] if len(course.xpath('./@data-coursename')) > 0 else ''
        course_url = 'https://xuexi.boxuegu.com{}'.format(course.xpath('./@data-url')[0]) if len(
            course.xpath('./@data-url')) > 0 else ''

        if course_url and course_name:
            course_dict = {}
            course_dict["course_name"] = course_name
            course_dict["course_url"] = course_url
            if not course_dict in course_name_urls:
                course_name_urls.append(course_dict)

    return course_name_urls

def parse_all_courses(driver):
    """获取所报的所有课程的url地址"""
    # 进入 "我的课程"
    my_classes = driver.find_element_by_id("myClass")
    my_classes.click()

    # 进入 "就业课"
    driver.find_element_by_id("xx2").click()

    course_name_urls = parse_course_name_url(driver)
    print(course_name_urls)

    time.sleep(1)

    # 进入微课
    driver.find_element_by_id("xx3").click()

    course_name_urls.extend(parse_course_name_url(driver))
    print(course_name_urls)

    # 微课可能有下一页
    while True:
        try:
            next = driver.find_element_by_xpath('//a[@class="next"]')
        except:
            break
        else:
            next.click()
            time.sleep(1)
            course_name_urls.extend(parse_course_name_url(driver))

    return course_name_urls


def parse_course_list(driver, course_id, fl):
    """解析课程列表页"""
    html = etree.HTML(driver.page_source)
    # 课程名称
    class_name = html.xpath('//h4/text()')[0]
    fl.write(class_name + '\n')
    # 以课程阶段进行分类
    stages = html.xpath('//div[@class="mrcroStageWarp"]')
    course_info_list = []
    for stage in stages:
        # 阶段1: 爬虫阶段
        stage_name = stage.xpath('./div[contains(@class, "mrcroStage")]/span/text()')[0]
        fl.write(' '*2 + stage_name + '\n')
        # 以每个课程进行分类
        courses = stage.xpath('.//div[@class="StageModuleCont"]')
        for course in courses:
            # https://xuexi.boxuegu.com/video.html?courseId=1131&moduleId=101759&type=PATH&phaseId=733
            # 课程名
            lesson_name = course.xpath('./p[@class="StageModuleName"]/text()')[0]
            # 阶段课程id
            phase_id = course.xpath('./a/@data-phaseid')
            if len(phase_id) > 0:
                phase_id = phase_id[0]
            else:
                break
            module_id = course.xpath('./a/@data-id')[0]
            course_url = 'https://xuexi.boxuegu.com/video.html?courseId={}&moduleId={}&type=PATH&phaseId={}'.format(course_id, module_id, phase_id)
            course_info = {
                "class_name": class_name.replace(':','').replace('/',' ').replace('【','_').replace('】','_').replace('__','_').replace('+','').replace('.','_'),
                "stage_name": stage_name.replace(':','').replace('/',' ').replace('【','_').replace('】','_').replace('__','_').replace('+','').replace('.','_'),
                "lesson_name": lesson_name.replace(':','').replace('/',' ').replace('【','_').replace('】','_').replace('__','_').replace('+','').replace('.','_'),
                "course_url": course_url,
            }

            fl.write(' '*4 + lesson_name + '\n')
            # print(course_info)

            course_info_list.append(course_info)
            parse_course_detail(driver, course_url, fl)

    return course_info_list

def parse_course_detail(driver, course_url, fl):
    """依次打开视频播放页, 获取视频列表信息"""

    driver.get(course_url)
    html = etree.HTML(driver.page_source)

    sections = html.xpath('//div[@class="video_list_warp"]')
    for section in  sections:
        section_name = section.xpath('./p/span/text()')[0]
        fl.write(' '*6 + section_name + '\n')
        course_names = section.xpath('./ul/li/p/text()')
        for course_name in course_names:
            fl.write(' '*8 + course_name + '\n')

def main():
    # 微博登录账号, 登录时需要输入验证码, 此时必须要显示图片
    username = '18811111111'
    password = '18811111111'
    # 博学谷登录账号
    # username = '15211111111'
    # password = '15211111111'

    driver = get_driver(username)
    url = 'https://www.boxuegu.com/'

    open_page(driver, url)
    if username.startswith("188"):
        weibo_login_boxuegu(driver, username, password)
    elif username.startswith("152"):
        login_boxuegu(driver, username, password)

    time.sleep(3)
    # 获取所有课程的url
    course_name_urls = parse_all_courses(driver)
    print(course_name_urls)

    # 首先手动获取想要提取课程信息的url地址
    # course_name_urls = [
    #     'https://xuexi.boxuegu.com/class_track.html?courseId=1131&isFree=1',
    #     'https://xuexi.boxuegu.com/class_track.html?courseId=1121&isFree=1'
    # ]

    for course_name_url in course_name_urls:
        course_name = course_name_url["course_name"]
        course_url = course_name_url["course_url"]
        print(course_url)
        if not course_url:  # 不知为何总出现一个为 None 的元素
            continue
        course_id = re.search(r'\d+', course_url).group()
        driver.get(course_url)
        time.sleep(3)
        fl = open('{}_{}_{}_content.txt'.format(username[:3], course_id, course_name.replace('/', '')), 'w', encoding='utf-8')
        course_info_list = parse_course_list(driver, course_id, fl)
        print(course_info_list)
        fl.close()


if __name__ == '__main__':
    main()




