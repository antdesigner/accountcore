

### Locust 环境配置

#### 安装

Python 2.7:

    $ python -m pip install locustio

Python 3:

    $ python3 -m pip install locustio

#### 运行

    $ locust -f locustfile.py --host=http://localhost:8069

#### 注意

在 on_start(self): 方法中
        # 数据库需要改变成自己的
        dbname = 'accountcore'

user可能也需要修改
        users = [
            {'user': 'user001', 'pass': 'user001', 'uid': 7},
            {'user': 'user002', 'pass': 'user002', 'uid': 8},
            {'user': 'user003', 'pass': 'user003', 'uid': 9},
            {'user': 'user004', 'pass': 'user004', 'uid': 10},
        ]