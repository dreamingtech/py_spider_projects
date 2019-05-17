# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from scrapy.pipelines.images import ImagesPipeline


class JavSpiderPipeline(object):
    def process_item(self, item, spider):
        print(json.dumps(item))
        return item

# 自定义图片下载处理的中间件
class JavImagesPipeline(ImagesPipeline):
    # 重写函数, 改写item处理完成的函数
    def item_completed(self, results, item, info):
        # result是一个list的结构. 可以获取多个图片保存的信息. 但由于使用yield, 一次只传递过一个item, 所以这里的result中只有一个元素.
        for key, value in results:
            try:
                image_urls_path = value.get('path','')
            except Exception as e:
                image_urls_path = ''
        item["image_urls_path"] = image_urls_path
        # 在完成处理后一定要返回item, 这样数据才能被下一个pipeline接收并处理.
        # 在此处添加断点再次进行调试, 看item中是否保存了图片下载的路径.
        return item

    def file_path(self, request, response=None, info=None):

        # check if called from image_key or file_key with url as first argument
        if not isinstance(request, Request):
            url = request
        else:
            url = request.url
        # 列表页图
        # https://jp.netcdn.space/digital/video/2wpvr00173/2wpvr00173ps.jpg
        # 详情页大图
        # https://jp.netcdn.space/digital/video/h_1290dovr00021/h_1290dovr00021pl.jpg
        # 演员图
        # https://jp.netcdn.space/mono/actjpgs/misaki_kanna.jpg
        # 展示图片大图
        # https://jp.netcdn.space/digital/video/h_1290dovr00021/h_1290dovr00021jp-1.jpg
        # 展示图片缩略图
        # https://jp.netcdn.space/digital/video/h_1290dovr00021/h_1290dovr00021-1.jpg

        image_guid = re.split(r'\.|/', url)[-3]
        # image_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
        return '%s.jpg' % (image_guid)