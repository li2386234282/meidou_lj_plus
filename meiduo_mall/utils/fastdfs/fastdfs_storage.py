"""
自定义django存储后端，修改ImageField类型字段url属性输出的结果
"""

from django.core.files.storage import Storage
from django.conf import settings


class FastDFSStorage(Storage):

    def open(self, name, mode='rb'):
        # 我们这里返回None，表示无需打开本地文件因为我们不把文件存储本地
        return None

    def save(self, name, content, max_length=None):
        # 该方法决定了图片如何存储，将来我们需要在此填充代码
        # 实现把图片上传到fdfs中
        pass

    def url(self, name):
        # 该函数返回到结果就是，ImageField.url属性的出的结果
        # 参数：name就是该文件类型字段在mysql中存储的，如：group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429

        return settings.FDFS_URL + name