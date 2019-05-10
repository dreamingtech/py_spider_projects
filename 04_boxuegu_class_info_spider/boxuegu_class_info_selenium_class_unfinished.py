import re
import time

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BoxueguClassInfoSpider(object):
    """博学谷所有课程信息爬虫"""

    def __init__(self):
        # 微博登录账号, 登录时需要输入验证码, 此时必须要显示图片

        # 以字典格式存储课程的名称和url
        # Python+人工智能在线就业班
        # https://xuexi.boxuegu.com/class_track.html?courseId=1121&isFree=1
        self.course_name_urls = []
        # 存储具体每一节课程url信息
        # https://xuexi.boxuegu.com/video.html?courseId=1121&moduleId=101919&type=PATH&phaseId=712
        self.video_play_urls = []
        
    def get_driver(self, username):

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
        driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=options)

        return driver

    def get_page(self, url):
        self.driver.get(url)
        if url.startswith("https://www.boxuegu.com"):
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "my-class")
                ))
        elif url.startswith("https://xuexi.boxuegu.com/class_track.html"):
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "mrcroStageWarp")
                ))
        elif url.startswith("https://xuexi.boxuegu.com/video.html"):
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "video_list_warp")
                ))

    def close_promotion_info(self):
        """关闭促销信息"""
        try:
            self.driver.find_element_by_xpath('//img[@class="february-close"]').click()
            time.sleep(1)
        except:
            pass

    def login(self):
        """使用博学谷账号登录"""
        self.driver.find_element_by_id("login-button").click()
        time.sleep(2)
        self.driver.find_element_by_xpath('//input[@class="cyinput1 form-control userName"]').send_keys(self.username)
        time.sleep(1)

        self.driver.find_element_by_xpath('//input[@class="cyinput2 form-control password"]').send_keys(self.password)
        time.sleep(1)

        self.driver.find_element_by_xpath('//button[@class="cymyloginbutton goLogin"]').click()


    def login_va_weibo(self):
        """使用微博账号登录"""

        self.driver.find_element_by_id("login-button").click()
        time.sleep(1)

        self.driver.find_element_by_xpath('//div[@class="weibo-login"]').click()
        time.sleep(1)

        self.driver.find_element_by_id("userId").send_keys(self.username)
        time.sleep(1)

        self.driver.find_element_by_id("passwd").send_keys(self.password)
        time.sleep(1)

        # 手动输入验证码
        captcha_input = self.driver.find_element_by_xpath('//input[@class="WB_iptxt oauth_form_input oauth_form_code"]')
        captcha = input("请输入验证码: ")
        captcha_input.send_keys(captcha)

        self.driver.find_element_by_xpath('//a[@class="WB_btn_login formbtn_01"]').click()

    def parse_course_name_url(self):
        """从就业班, 微课列表中解析出课程名称和url"""
        html = etree.HTML(self.driver.page_source)
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
                # 有可能会提取到重复的课程
                if not course_dict in self.course_name_urls:
                    self.course_name_urls.append(course_dict)
                    
        time.sleep(1)

    def parse_next_page(self):
        """解析就业班和微课的下一页"""
        while True:
            try:
                next = self.driver.find_element_by_xpath('//a[@class="next"]')
            except:
                break
            else:
                next.click()
                time.sleep(1)
                self.parse_course_name_url()
        time.sleep(1)

    def parse_all_courses(self):
        """获取所报的所有课程的url地址"""
        # 进入 "我的课程"
        time.sleep(1)
        self.driver.find_element_by_id("myClass").click()

        # 进入 "就业课"
        self.driver.find_element_by_id("xx2").click()
        time.sleep(1)
        self.parse_course_name_url()

        # 可能存在下一页
        self.parse_next_page()

        # 进入微课
        self.driver.find_element_by_id("xx3").click()
        time.sleep(1)

        self.parse_course_name_url()
        # 可能存在下一页
        self.parse_next_page()

    def parse_course_list(self):
        """解析课程列表页"""
        html = etree.HTML(self.driver.page_source)

        course_id = re.search(r'\d+', self.driver.current_url).group()
        # 课程名称
        class_name = html.xpath('//h4/text()')[0]
        self.file.write(class_name + '\n')
        # 以课程阶段进行分类
        stages = html.xpath('//div[@class="mrcroStageWarp"]')

        for stage in stages:
            # 阶段1: 爬虫阶段
            stage_name = stage.xpath('./div[contains(@class, "mrcroStage")]/span/text()')[0]
            self.file.write(' ' * 2 + stage_name + '\n')
            # 以每个课程进行分类
            courses = stage.xpath('.//div[@class="StageModuleCont"]')
            for course in courses:
                # https://xuexi.boxuegu.com/video.html?courseId=1131&moduleId=101759&type=PATH&phaseId=733
                # 课程名
                lesson_name = course.xpath('./p[@class="StageModuleName"]/text()')
                module_id = course.xpath('./a/@data-id')   # 可能会提取不到
                phase_id = course.xpath('./a/@data-phaseid')

                # print(lesson_name, module_id, phase_id, sep='\n')

                if len(phase_id) * len(lesson_name) * len(module_id) > 0:
                    phase_id = phase_id[0]
                    lesson_name = lesson_name[0]
                    module_id = module_id[0]
                else:
                    break
                video_play_url = 'https://xuexi.boxuegu.com/video.html?courseId={}&moduleId={}&type=PATH&phaseId={}'.format(
                    course_id, module_id, phase_id)

                self.file.write(' ' * 4 + lesson_name + '\n')
                self.video_play_urls.append(video_play_url)

    def parse_course_detail(self):
        """依次打开视频播放页, 获取视频列表信息"""

        html = etree.HTML(self.driver.page_source)

        sections = html.xpath('//div[@class="video_list_warp"]')
        for section in sections:
            section_name = section.xpath('./p/span/text()')[0]
            self.file.write(' ' * 6 + section_name + '\n')
            lesson_names = section.xpath('./ul/li/p/text()')
            for lesson_name in lesson_names:
                self.file.write(' ' * 8 + lesson_name + '\n')

def main():
    # 1. 实例化爬虫
    bxg = BoxueguClassInfoSpider()
    bxg.base_url = 'https://www.boxuegu.com/'
    # 微博登录账号, 登录时需要输入验证码, 此时必须要显示图片
    username = '18811111111'
    password = '18811111111'
    # 博学谷登录账号
    # username = '15211111111'
    # password = '15211111111'

    # 2. 获取 driver 对象
    bxg.driver = bxg.get_driver(bxg.username)
    # 3. 打开主页
    bxg.get_page(bxg.base_url)
    # 4. 关闭促销信息
    bxg.close_promotion_info()
    # 5. 登陆博学谷
    if bxg.username.startswith("188"):
        bxg.login_va_weibo()
    elif bxg.username.startswith("152"):
        bxg.login()

    # 6. 获取所有课程的信息
    bxg.parse_all_courses()
    # 7. 解析课程列表页
    for course_name_url in bxg.course_name_urls:
        course_name = course_name_url["course_name"]
        course_url = course_name_url["course_url"]
        print(course_url)
        if not course_url:  # 不知为何总出现一个为 None 的元素
            continue
        course_id = re.search(r'\d+', course_url).group()
        bxg.file = open('{}_{}_{}_content.txt'.format(bxg.username[:3], course_id, course_name.replace('/', '')), 'a+', encoding='utf-8')
        bxg.get_page(course_url)
        time.sleep(1)
        bxg.parse_course_list()
        time.sleep(1)

        # 8. 解析视频播放页, 获取课程详情信息
        for video_play_url in bxg.video_play_urls:
            bxg.get_page(video_play_url)
            time.sleep(1)
            bxg.parse_course_detail()
        # 每个课程解析完成后把视频播放地址重置为空
        bxg.video_play_urls = []
        bxg.file.close()

if __name__ == '__main__':
    main()