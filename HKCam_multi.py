# coding=utf-8
import os
import platform
# from cv2 import waitKey
from HCNetSDK import *
from PlayCtrl import *
import numpy as np
import time
import cv2
import threading

class HKCam_mul(object):
    def __init__(self,camIPs,usernames,passwords,devport=8000,recorder = False):
        # 登录的设备信息
        self.DEV_IPs = [create_string_buffer(camIP.encode()) for camIP in camIPs]
        self.DEV_PORT =devport # 所有相机摄像头端口必须要一致
        self.DEV_USER_NAMEs= [create_string_buffer(username.encode()) for username in usernames]
        self.DEV_PASSWORDs = [create_string_buffer(password.encode()) for password in passwords]
        self.WINDOWS_FLAG = False if platform.system() != "Windows" else True
        self.funcRealDataCallBack_V30 = None
        self.last_stamp = None #上次时间戳
        self.FuncDecCB = DECCBFUNWIN(self.DecCBFun) #公用解码回调函数
        self.lock = threading.RLock() #解码回调时需要枷锁否则会出现通道混乱
        self.recent_imgs = {} #用于保存每一路视频的时间戳和rgb图像
        # 加载库,先加载依赖库
        if self.WINDOWS_FLAG:
            os.chdir(r'./lib/win')
            self.Objdll = ctypes.CDLL(r'./HCNetSDK.dll')  # 加载网络库
            self.Playctrldll = ctypes.CDLL(r'./PlayCtrl.dll')  # 加载播放库
        else:
            os.chdir(r'./lib/linux')
            self.Objdll = cdll.LoadLibrary(r'./libhcnetsdk.so')
            self.Playctrldll = cdll.LoadLibrary(r'./libPlayCtrl.so')
        # 设置组件库和SSL库加载路径    
        self.SetSDKInitCfg()
        # 初始化DLL
        self.Objdll.NET_DVR_Init()
        # 启用SDK写日志
        self.Objdll.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)
        os.chdir(r'../../') 
        self.lUserIds= []       # 信号源id 
        self.lRealPlayHandles =[]#信号源句柄
        self.PlayCtrl_Ports =[]# 播放句柄
        self.get_preview_info()
        self.load_cameras()  #登录设备
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)
        for idex,userid in enumerate(self.lUserIds):     
            PlayCtrl_Port = c_long(-1)  # 播放句柄
            if  not self.Playctrldll.PlayM4_GetPort(byref(PlayCtrl_Port)):
                #print('asgdsagewgg',PlayCtrl_Port)
                print(u'获取播放库句柄失败')
            else:
                print('获取播放库句柄成功',PlayCtrl_Port)
                self.PlayCtrl_Ports.append(PlayCtrl_Port)            
            lRealPlayHandle = self.Objdll.NET_DVR_RealPlay_V40(userid, byref(self.preview_info), None, idex)            
            if not lRealPlayHandle:
                print('lReadlHandle 加载失败')
            print('lRealPlayHandle',lRealPlayHandle)
            if recorder: # 视频录像
                string_buf = f'test{userid}.mp4'
                if not self.Objdll.NET_DVR_SaveRealData(lRealPlayHandle, create_string_buffer(string_buf.encode())):
                    print('录像失败')
            self.lRealPlayHandles.append(lRealPlayHandle)
        print(self.PlayCtrl_Ports)
        for idd,item in enumerate(self.lRealPlayHandles):
             self.Objdll.NET_DVR_SetRealDataCallBack(item,self.funcRealDataCallBack_V30,idd)
        time.sleep(2)
    
    def read(self,):
        #cv2.waitKey(40)
        return  self.recent_imgs
        
    def RealDataCallBack_V30(self,lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
         idx = pUser if pUser else 0
        # 码流回调函数
         if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.Playctrldll.PlayM4_SetStreamOpenMode(self.PlayCtrl_Ports[idx], 0)
            # 打开码流，送入40字节系统头数据
            if self.Playctrldll.PlayM4_OpenStream(self.PlayCtrl_Ports[idx], pBuffer, dwBufSize, 1024*1024):
                # 设置解码回调，可以返回解码后YUV视频数据
                self.Playctrldll.PlayM4_SetDecCallBackExMend(self.PlayCtrl_Ports[idx], self.FuncDecCB, None, 0, None)
                # 开始解码播放
                if self.Playctrldll.PlayM4_Play(self.PlayCtrl_Ports[idx], None):
                    print(u'播放库播放成功',self.PlayCtrl_Ports[idx],lPlayHandle)
                else:
                    print(u'播放库播放失败')
            else:
                print(u'播放库打开流失败')
         elif dwDataType == NET_DVR_STREAMDATA:
            self.Playctrldll.PlayM4_InputData(self.PlayCtrl_Ports[idx], pBuffer, dwBufSize)
         else:
            print (u'其他数据,长度:', dwBufSize)

    def load_cameras(self,):
        # 登录注册设备
        device_info = NET_DVR_DEVICEINFO_V30()
        for dev_ip,dev_name,password in zip(self.DEV_IPs,self.DEV_USER_NAMEs,self.DEV_PASSWORDs):
            lUserId = self.Objdll.NET_DVR_Login_V30(dev_ip,self.DEV_PORT,dev_name,password, byref(device_info))
            if lUserId>=0:
                print(f'摄像头[{dev_ip.raw.decode()}]登录成功!!')
            self.lUserIds.append(lUserId)
    def get_preview_info(self,):
        self.preview_info = NET_DVR_PREVIEWINFO()
        self.preview_info.hPlayWnd = 0
        self.preview_info.lChannel = 1  # 通道号
        self.preview_info.dwStreamType = 0  # 主码流
        self.preview_info.dwLinkMode = 0  # TCP
        self.preview_info.bBlocked = 1  # 阻塞取流

    def SetSDKInitCfg(self,):
        # 设置SDK初始化依赖库路径
        # 设置HCNetSDKCom组件库和SSL库加载路径
        # print(os.getcwd())
        if self.WINDOWS_FLAG:
            strPath = os.getcwd().encode('gbk')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
        else:
            strPath = os.getcwd().encode('utf-8')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))

    def DecCBFun(self,nPort, pBuf, nSize, pFrameInfo, nUser, nReserved2):
            self.lock.acquire() #解码前要先枷锁
            if pFrameInfo.contents.nType == 3:
                # 如果有耗时处理，需要将解码数据拷贝到回调函数外面的其他线程里面处理，避免阻塞回调导致解码丢帧
                nWidth = pFrameInfo.contents.nWidth
                nHeight = pFrameInfo.contents.nHeight
                #nType = pFrameInfo.contents.nType
                dwFrameNum = pFrameInfo.contents.dwFrameNum
                nStamp = pFrameInfo.contents.nStamp
                if self.recent_imgs.get(nPort):
                    # if True:
                    #     print(nPort,self.recent_imgs.get(nPort)[0]-nStamp)
                    if self.recent_imgs.get(nPort)[0]!=nStamp: #判定时间戳,防止重复解码消耗系统资源
                        YUV = np.frombuffer(pBuf[:nSize],dtype=np.uint8)
                        YUV = np.reshape(YUV,[nHeight+nHeight//2,nWidth])
                        img_rgb = cv2.cvtColor(YUV,cv2.COLOR_YUV2BGR_YV12)
                        #cv2.putText(img_rgb,f'{dwFrameNum}',(50,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),4)
                        self.recent_imgs[nPort]=(nStamp,img_rgb)
                else:
                    YUV = np.frombuffer(pBuf[:nSize],dtype=np.uint8)
                    YUV = np.reshape(YUV,[nHeight+nHeight//2,nWidth])
                    img_rgb = cv2.cvtColor(YUV,cv2.COLOR_YUV2BGR_YV12)
                    self.recent_imgs[nPort]=(nStamp,img_rgb)
                self.lock.release() #释放锁
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    def release(self):
        for item in self.lRealPlayHandles:
            self.Objdll.NET_DVR_StopRealPlay(item)
        for item in self.PlayCtrl_Ports:
            print(item.value)
            if item.value > -1:
                self.Playctrldll.PlayM4_Stop(item)
                self.Playctrldll.PlayM4_CloseStream( item)
                self.Playctrldll.PlayM4_FreePort(item)
                PlayCtrl_Port = c_long(-1)
        for item in self.lUserIds:
            self.Objdll.NET_DVR_Logout(item)
        self.Objdll.NET_DVR_Cleanup()
        print('释放资源结束')

if __name__=="__main__":    
    # for ii in range(6):
    #     cv2.namedWindow(f'{ii}',0)
    camIPS =['192.168.3.151',
                '192.168.3.157',   
                '192.168.3.167',
                '192.168.3.119',                       
                '192.168.3.162',
                '192.168.3.103']
    usernames =['admin']*6
    passwords = ['admin']*6

    hkcam_muls = HKCam_mul(camIPS,usernames,passwords)
    while True:
        t0 = time.time()
        imgs = hkcam_muls.read()
        for key in imgs.keys():
            stamp,img = imgs[key]
            cv2.imshow(f'{key}',cv2.resize(img,(800,600)))
            kkk =cv2.waitKey(1)
        if kkk==ord('q'):
            break
    hkcam_muls.release()
