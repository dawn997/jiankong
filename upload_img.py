import paramiko
def ssh_scpHtmlfile(filename):
    localFile = r'./' + filename + '.jpg'
    targetFile = '/var/www/html/' + filename + '.jpg'
    transport=paramiko.Transport(('107.172.86.106',22))
    transport.connect(username='root',password='I1Q0xNO6j0kxyQJg67')
    sftp=paramiko.SFTPClient.from_transport(transport)
    sftp.put(localFile,targetFile)  #上传
    print("success")
    transport.close()