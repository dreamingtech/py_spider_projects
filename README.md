# 爬虫项目集合

## 01 天善智能课程爬虫

### 需求分析

requests实现爬取天善智能所有课程信息. 反爬措施非常弱, 可以不用考虑反爬.

### 难点

课程是从 "课程形式", "课程方向"和"课程标签" 三个不同的方面进行分类的, 如何获取某个课程对应的这三个分类信息. 解决方法, 设置三个以大分类名为名称的字段, 分别保存这三个大分类的信息. 对三个大分类中每个小分类进行遍历, 记录下每个小分类的课程详情url地址, 同时把此课程对应的分类字段的值设置为小分类的名称.

## 02  在线视频下载

### 需求

国外sci_exp学习网站上有大量的理工科学习资源, 但是需要付费才能观看和下载, 并且付费价格不是一般的贵. 使用selenium+chrome自动下载网站视频.

## 实现功能:

视频重命名为 ”上传日期_标题_视频id_原始视频名称” 的形式, 保存到上传年份为名的文件夹中, 视频缩略图的下载, 视频基本信息的提取. 写入视频信息到本地与视频同名的txt文件中, 保存视频信息到mysql数据库中.

### 难点

1. 网站的登录和认证方式不同于其它的网站, 无法使用requests的session模拟登录. 如果使用requests, 则必须要在每个requests中都加入HTTPBasicAuth进行认证. 使用selenium+chrome却可以绕过这个问题.
2. 网站的反爬机制, 使用requests库下载视频时大约10个小时就会被网站禁止一次. 但使用selenium+chrome就能完全模拟浏览器的行为, 从而绕过网站的反爬机制.
3. 想要实现在视频下载链接上点击右键从右键菜单中选择"另存为", 然后重命名保存的视频名称和地址, 再点击保存. 但selenium无法操作鼠标右键和windows对话框, 使用pywin32模块和AutoIT来操作鼠标右键及windows对话框, 选择"另存为", 及视频的重命名.
4. 网站被国内屏蔽, 需要使用国外代理地址才能正常访问和下载, 这里使用shadowsocks客户端实现代理.



## 03 豆瓣图书爬虫

### 需求分析

爬取豆瓣图书所有图书信息并保存到json文件中.

### 难点

页面结束页的确认. 页面显示的图书数量与实际的图书数量不符合, 只能从页面本身的结构特点进行判断, 如果页面中提取不到图书信息, 就认为图书列表页已到达最后一页.


## 04 博学谷所有已报课程信息爬虫

### 需求分析

爬取博学谷所报的所有课程的详情信息, 并写入到txt文件中.

### 难点

无压力, 只有一些小的细节需要注意. 
如微博登录时需要手动输入验证码
如果出现促销信息, 需要先关闭才能进行登录
写入到文件时课程名中可能存在着 '/'
在 "就业班", "微课" 中提取的课程信息可能会出现重复的
无原因的提取到课程url为None的信息


## 05 博学谷所有就业班课程信息爬虫

### 需求分析

爬取博学谷所有就业班课程的详情信息, 并写入到txt文件中.

博学谷所有就业班课程的url地址格式如下, 可以使用遍历从0开始尝试, 如果地址存在, 就把能够 "免费试学" 的章节的详细章节信息提取出来.
https://xuexi.boxuegu.com/class_track.html?courseId=1132&isFree=1
经过遍历, 得到有效的课程id列表为

[70, 76, 123, 135, 218, 220, 222, 237, 244, 274, 293, 309, 322, 328, 329, 435, 436, 469, 470, 486, 555, 587, 795, 802, 907, 909, 944, 954, 955, 956, 957, 958, 959, 969, 979, 981, 992, 994, 1017, 1022, 1047, 1083, 1092, 1109, 1110, 1111, 1112, 1113, 1114, 1120, 1121, 1123, 1125, 1126, 1127, 1128, 1129, 1131, 1132, 1133, 1136, 1146, 1168, 1169, 1170, 1173, 1180, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1198, 1199, 1200, 1222, 1230, 1234, 1258, 1259, 1276]

### 难点

只能提取到能够 "免费试学" 章节的详情信息, 其它的无法提取.

## 06 某视频网站视频信息爬虫

### 需求分析

国外某视频网站所有视频信息爬虫. 

### 难点

1. 服务器在国外, 需要使用代理才能下载
2. 4种语言的网站, 需要把4种语言的网站信息抓取下来进行整合. 
3. 由于4种语言的网站结构完全一致, 只有关键词不同, 可以构造出每一种语言对应的xpath语法规则, 根据语言的不同动态的生成xpath规则.

```python

language = re.match(r'.*.com/(.*?)/movie.*', response.url).group(1)

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

```

4. 确保当同一个视频的4种语言网站都爬取完之后才 yield item

```python
if  {"cn", "en", "ja", "tw"} == set(response.meta.get("category_dict", {}).keys()):
	yield meta
```

5. 发送同一个视频不同语言的请求

```python

for lan in ({"cn", "en", "ja", "tw"} - set(response.meta.get("category_dict", {}).keys())):
    if not lan == language:
        url_sign = re.match(r'https://javzoo.com/.*?/movie/(.*)', response.url).group(1)
        url = "https://javzoo.com/{}/movie/{}".format(lan,url_sign)
        yield scrapy.Request(url=url, callback=self.parse_detail, meta=meta)

```

### 进一步改进

使用代理
下载图片
保存到数据库中
增量爬虫
分布式爬虫