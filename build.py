# -*- coding: utf-8 -*

import os

import hashlib
import sys
import os, sys, time
from paramiko import SSHClient, SFTPClient, AutoAddPolicy
import pickle


class SshServer(object):

  def __init__(self, ip=None, port=22, user='root', password=None):
    """

    :param ip: 服务器ip地址
    :param port: 服务器端口 ssh端口默认22
    :param user: 服务器登录账户
    :param password: 服务器登录密码
    """
    if ip is None:
      raise Exception('服务器ip不能为空')
    self._ip = ip
    self._port = port
    self._user = user
    if password is None:
      raise Exception(u'密码不能为空')
    self._password = password
    self.ssh = SSHClient()

    self.isConnect = False
    try:
      self._connect()
      self.isConnect = True
      print("连接成功")
    except:
      self.isConnect = False
      print("连接失败")

  def _connect(self):
    """
    ssh远程连接服务器
    :return:
    """
    self.ssh.set_missing_host_key_policy(AutoAddPolicy())
    self.ssh.connect(self._ip, self._port, self._user, self._password)

  def ssh_cmd(self, cmd):
    """
    发送命令到服务器
    :param cmd:
    :return:
    """
    if not self.isConnect:
      self._connect()
      result = self.ssh.exec_command(cmd)
    else:
      print("cmd:" + cmd)
      result = self.ssh.exec_command(cmd)

    return result

  def _getSftp(self):
    sftp = SFTPClient.from_transport(self.ssh.get_transport())
    sftp = self.ssh.open_sftp()
    return sftp

  def ssh_scp_put(self, local_file, remote_file, callback):
    '''
    本地文件上送到服务器
    :param local_file: 本地文件路径
    :param remote_file: 服务器文件路径
    :param callback: 上送回调 def(current,total): current当前,total文件总大小
    :return:
    '''
    self._getSftp().put(local_file, remote_file, callback=callback)

  def ssh_scp_get(self, remote_file, local_file, callback):
    '''
    服务器文件下载到本地
    :param remote_file: 服务器远程文件路径
    :param local_file: 本地文件路径
    :param callback: 下载回调 def(current,total): current当前,total文件总大小
    :return:
    '''
    self._getSftp().get(remote_file, local_file, callback=callback)


def calcFileMd5(filename, slim=10 * 1024 * 1024):
  '''
  计算文件md5值
  :param filename: 需要计算的文件
  :param slim: 计算文件的限制，超出将分割计算
  :return: md5值
  '''
  _slim = slim
  hmd5 = hashlib.md5()
  fp = open(filename, "rb")
  f_size = os.stat(filename).st_size
  if f_size > _slim:
    while f_size > _slim:
      hmd5.update(fp.read(_slim))
      f_size /= _slim

    if (f_size > 0) and (f_size <= _slim):
      hmd5.update(fp.read())
  else:
    hmd5.update(fp.read())
  return hmd5.hexdigest()


def cpFile(srcFile, targetFile):
  """
  拷贝文件
  :param srcFile: 源文件
  :param targetFile: 目标文件
  :return:
  """

  # 如果目标文件不存在,或者存在但md5值不同,则覆盖
  if not os.path.exists(targetFile) or (
    os.path.exists(targetFile) and calcFileMd5(targetFile) != calcFileMd5(srcFile)):
    open(targetFile, "wb").write(open(srcFile, "rb").read())


def iterateFile(psrc, ptarget):
  """
   遍历文件拷贝
  :param psrc:源目录
  :param ptarget:目标目录
  :return:
  """
  for f in os.listdir(psrc):
    srcFile = os.path.join(psrc, f)
    targetFile = os.path.join(ptarget, f)

    if os.path.isdir(srcFile):
      if not os.path.exists(targetFile):
        os.makedirs(targetFile)
      iterateFile(srcFile, targetFile)
    elif os.path.isfile(srcFile):
      cpFile(srcFile, targetFile)


md5dict = {}  # 保存上传服务器文件的md5值


def iterateCreateDir2Server(local, sshServer, absoluteLocalPath, absoluteServerPath):
  '''
  在服务器上创建本地对应路径
  :param local:
  :param sshServer:SshServer对象
  :param absoluteLocalPath:本地绝对路径
  :param absoluteServerPath:服务器绝对路径
  :return:
  '''
  for f in os.listdir(local):
    file = os.path.join(local, f)
    if os.path.isdir(file):
      serverDir = absoluteServerPath + file.replace(absoluteLocalPath, '').replace('\\', '/')
      print("server path:" + serverDir)
      sshServer.ssh_cmd('mkdir %s' % serverDir)


def iterateCopy2Server(local, sshServer, absoluteLocalPath, absoluteServerPath, md5File):
  '''
   拷贝本地文件到服务器
  :param local: 文件路径
  :param sshServer: SshServer对象
  :param absoluteLocalPath: 本地绝对路径
  :param absoluteServerPath: 服务器绝对路径
  :param md5File: 文件MD5值记录文件
  :return:
  '''
  for f in os.listdir(local):
    file = os.path.join(local, f)
    if os.path.isdir(file):
      iterateCopy2Server(file, sshServer, absoluteLocalPath, absoluteServerPath, md5File)

    else:
      serverFile = file.replace(absoluteLocalPath, '').replace('\\', '/')
      serverPathFile = absoluteServerPath + serverFile
      print("server file:" + serverPathFile)
      # open('file_md5.txt','rb')
      print('file:' + file + ",md5:" + calcFileMd5(file))
      if os.path.exists(md5File):  # md5值文件存在，需要对比md5值
        md5 = {}
        with open(md5File, 'rb') as f:
          md5 = pickle.load(f)
        if (str(file) in md5) and md5[str(file)] == calcFileMd5(file):  # md5值不存在或者 md5值相同，说明文件已经上传过服务器，不需要重复上传
          print(str(file) + u",md5值文件相同或md5值文件,不需要上传")
        else:
          print(str(file) + u",md5值文件不相同,需要上传")
          md5dict[str(file)] = calcFileMd5(file)
          sshServer.ssh_scp_put(file, serverPathFile, None)
      else:  # md5值不存在，全部上传
        print(str(file) + ",md5值文件不存在，上传")
        md5dict[str(file)] = calcFileMd5(file)
        sshServer.ssh_scp_put(file, serverPathFile, None)


ip = "your server ip"
user = "your server user"
password = "your server password"
port = "22"  # ssh默认端口22,一般不需要修改
buildDir = "you build dir"  # 编译后保存的目录
serverPath = '/var/www'  # 服务器保存路径地址
if __name__ == "__main__":
  workSrc = os.getcwd()  # python所在目录
  os.chdir(workSrc)  # 工作路径移动到当前b路径，执行npm run build编译命令
  md5File = workSrc + '/file_md5.txt'  # md5文件保存在工作目录，比较md5值，比较相同文件重复上传
  sshServer = SshServer(ip=ip, port=port, user=user, password=password)  # 建个远程连接
  psrc = os.path.join(workSrc, "dist")
  #
  ptarget = os.path.join(workSrc, buildDir)
  result = os.system("npm run build")
  if result == 0:  # 编译完成
    iterateFile(psrc, ptarget)  # 编译后资源文件夹拷贝
    print(u"拷贝完成")
    sshServer.ssh_cmd('mkdir ' + serverPath + '/' + buildDir)
    iterateCreateDir2Server(ptarget, sshServer, workSrc, serverPath)
    print("服务器路径创建完成")
    iterateCopy2Server(ptarget, sshServer, workSrc, serverPath, md5File)

    # 拷贝服务器完成后，记录上传的文件md5值
    print("服务器上送完成")
    with open(md5File, 'wb') as f:
      pickle.dump(md5dict, f)
    print("md5值记录完成")
  print("操作完成")
