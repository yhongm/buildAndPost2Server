# 一行命令解决vuejs编译上传服务器一系列操作
# 在项目根目录执行python build.py 即可执行编译以及编译后文件上传到服务器的一些列操作
# 对比文件md5值，相同文件不重复上传
## 使用方法：
1. 首先在 build.py内配置一下内容
```
ip = "your server ip" 需要上传的服务器ip地址
user = "your server user" 服务器登录账号
password = "your server password" 服务器登录密码
port = "22"  # ssh默认端口22,一般不需要修改
buildDir = "you build dir" #编译后保存的目录名
serverPath = '/var/www'  # 服务器保存路径地址
```
2. 将build.py拷贝到vuejs项目根目录,执行python build.py即可编译上传

