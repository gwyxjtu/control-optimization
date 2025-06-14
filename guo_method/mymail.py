import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

# SMTP 服务商信息
host='smtp.163.com'
port=465

# 发送账户信息
sender='kezhi_server@163.com'
passward='RQBKDOWOZGHSQOHB'

def GenMessage(Subject:str,From:str,To:str,text,file_list:list=[]):
    # 生成一个带附件的邮件对象
    message=MIMEMultipart()

    # 添加邮件头信息
    message['Subject']=Subject
    message['From']=From
    message['To']=To

    # 写入邮件正文
    message.attach(MIMEText(text,'html','utf-8'))

    # 添加附件
    if file_list==[]:
        return message
    else:
        for filepath in file_list:
            with open(filepath,'rb') as f:
                data=f.read()
            file=MIMEApplication(data)
            if '/' in filepath:
                filename=filepath[filepath.rfind('/')+1:]
            elif '\\' in filepath:
                filename=filepath[filepath.rfind('\\')+1:]
            else:
                filename=filepath
            file.add_header('Content-Disposition', 'attachment',filename=filename)
            message.attach(file)
    return message

    
def send(Subject:str,receivers:list,text:str,file_list:list=[]):
    for receiver in receivers:
        message=GenMessage(Subject,'<'+sender+'>','<'+receiver+'>',text,file_list)
        try:
            print('建立服务中........')
            server=smtplib.SMTP_SSL(host,port)
            print('服务建立成功\n正在登陆账户......')
            server.login(sender,passward)
            print('登录成功\n正在发送邮件')
            server.sendmail(sender,receiver,message.as_string())
            print('邮件发送成功')
            with open('send.log','a+',encoding='utf-8') as log:
                log.write(time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())+" send successfully From "+sender+" To "+receiver+'\n')
                log.close()
            server.quit()
        except smtplib.SMTPException as e:
            with open('send.log','a+',encoding='utf-8') as log:
                log.write(str(e))
                log.close()

if __name__=='__main__':
    receivers=['1538001851@qq.com']
    send('Text',receivers,'这是一封测试邮件',['./mymail.py'])