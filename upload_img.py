import paramiko
import os
def ssh_scpHtmlfile(filename):
    ip = os.environ.get("VPS_IP")
    password = os.environ.get("VPS_PASSWORD")
    localFile = r'./' + filename + '.jpg'
    targetFile = '/var/www/html/' + filename + '.jpg'
    transport=paramiko.Transport((ip,22))
    transport.connect(username='root',password=password)
    sftp=paramiko.SFTPClient.from_transport(transport)
    sftp.put(localFile,targetFile)  #上传
    print("success")
    transport.close()