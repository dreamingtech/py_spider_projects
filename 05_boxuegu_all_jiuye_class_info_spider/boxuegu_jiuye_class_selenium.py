import re
import time

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver():

    options = webdriver.ChromeOptions()
    # 不显示图片, 在需要关闭促销信息的时候, 必须要显示图片, 否则无法加载出关闭的按钮.
    # 在使用微博登录的时候要输入验证码, 必须要显示图片
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # options.add_argument("--proxy-server=socks5://127.0.0.1:1080")
    # 最大化窗口
    options.add_argument("start-maximized")

    # options.set_headless(headless=True)
    # 添加xpath插件
    # extension_path = r"D:/python_packages/XPath-Helper_v2.0.2.crx"
    # options.add_extension(extension_path)

    chrome_driver_path = r"D:\python_packages\chromedriver_win32_73.0.3683.68\chromedriver.exe"
    driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options = options)

    return driver

def ec_wait(driver, url):

    # 根据不同的url选择不同的等待方式

    if url.startswith("https://xuexi.boxuegu.com/class_track.html"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "StageModuleName")
                                                ))
    elif url.startswith("https://xuexi.boxuegu.com/video.html"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "video_list_warp")
                                                ))

def get_page(driver, url):
    # 这里不使用点击下一页的方式进行翻页, 因为下一页要解决等待的问题, 直接使用get就不会出现等待的问题
    driver.get(url)
    ec_wait(driver, url)

def check_exists(driver, url):
    # 这里不使用点击下一页的方式进行翻页, 因为下一页要解决等待的问题, 直接使用get就不会出现等待的问题
    driver.get(url)

    # ec_wait(driver, url)

    if driver.current_url != url:
        print("就业班地址不存在, 跳过")
        return False
    else:
        return True

def parse_course_name(driver):
    """解析出课程名称"""
    """解析课程列表页"""
    html = etree.HTML(driver.page_source)
    # 课程名称
    course_name = html.xpath('//h4/text()')[0]
    return course_name

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
            video_play_url = 'https://xuexi.boxuegu.com/video.html?courseId={}&moduleId={}&type=PATH&phaseId={}'.format(course_id, module_id, phase_id)

            fl.write(' '*4 + lesson_name + '\n')

            parse_course_detail(driver, video_play_url, fl)

def parse_course_detail(driver, video_play_url, fl):
    """依次打开视频播放页, 获取视频列表信息"""
    get_page(driver, video_play_url)
    html = etree.HTML(driver.page_source)

    sections = html.xpath('//div[@class="video_list_warp"]')
    for section in  sections:
        section_name = section.xpath('./p/span/text()')[0]
        fl.write(' '*6 + section_name + '\n')
        course_names = section.xpath('./ul/li/p/text()')
        for course_name in course_names:
            fl.write(' '*8 + course_name + '\n')

def main():

    # 博学谷登录账号
    username = '15211111111'
    password = '15211111111'

    driver = get_driver()
    url = 'https://www.boxuegu.com/'

    get_page(driver, url)
    
    login_boxuegu(driver, username, password)
    time.sleep(1)

    base_url = "https://xuexi.boxuegu.com/class_track.html?courseId={}"
    available_id_list = []
    id_list = [70, 76, 123, 135, 218, 220, 222, 237, 244, 274, 293, 309, 322, 328, 329, 435, 436, 469, 470, 486, 555, 587, 795, 802, 907, 909, 944, 954, 955, 956, 957, 958, 959, 969, 979, 981, 992, 994, 1017, 1022, 1047, 1083, 1092, 1109, 1110, 1111, 1112, 1113, 1114, 1120, 1121, 1123, 1125, 1126, 1127, 1128, 1129, 1131, 1132, 1133, 1136, 1146, 1168, 1169, 1170, 1173, 1180, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1198, 1199, 1200, 1222, 1230, 1234, 1258, 1259, 1276]
    # for course_id in range(0, 2000):
    for course_id in id_list:
        course_url = base_url.format(course_id)
        if check_exists(driver, course_url):
            print("就业班地址有效", course_url)
            course_name = parse_course_name(driver)
            time.sleep(1)
            print(course_id)
            available_id_list.append(course_id)
            fl = open('{}_{}_{}_content.txt'.format(username[:3], course_id, course_name.replace('/', '')), 'w',
                      encoding='utf-8')
            parse_course_list(driver, course_id, fl)
            fl.close()
        else:
            print("就业班地址无效", course_url)

    print(available_id_list)


if __name__ == '__main__':
    main()

