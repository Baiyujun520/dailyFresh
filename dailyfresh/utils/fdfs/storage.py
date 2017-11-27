from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    '''fast dfs 文件存储类'''
    def __init__(self, client_conf=None, base_url=None):
        '''初始nginx的ip的ip地址端口号,初始化客户端的路径'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self, name,  content):
        '''保存文件时使用'''
        # name 是你选择上传的文件的名称
        # content 就是包含你上传文件内容的文件对象File
        client = Fdfs_client(self.client_conf)

        ret = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        if ret.get('Status') != 'Upload successed.':
            raise Exception('文件上传失败')

        file_name = ret.get('Remote file_id')

        return file_name

    def exists(self, name):
        '''django判断文件是否存在，若存在返回True 若不存在返回False'''
        return False

    def url(self, name):
        # 返回已经上传图片在fdfs上的编码
        return self.base_url + name



