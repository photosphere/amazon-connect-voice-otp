import streamlit as st
import time
import random
import string
import boto3

connect_client = boto3.client("connect")

# 设置页面标题
st.title("语音验证码Demo")

# 生成随机验证码的函数
def generate_otp(length=6):
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))
# 发起一个外呼语音电话
def start_outbound_voice_call(
    phone_number,
    otp_code,
    connect_instance_id,
    contact_flow_id,
    source_phone_number=None
):
    try:
        # 初始化 Amazon Connect 客户端
        connect_client = boto3.client('connect')
        
        # 准备默认属性
        otp_msg="<speak><break time='1s'/>您的语音将验证码是<prosody rate='slow'><say-as interpret-as='digits'>"+otp_code+"</say-as></prosody></speak>"
        attributes = {'WarningMessage':otp_msg,"Language":'ZH'}
       
            
        # 添加验证码到属性中，以便在 Contact Flow 中使用
        attributes['otpCode'] = otp_code
        
        # 准备 API 调用参数
        params = {
            'DestinationPhoneNumber': phone_number,
            'ContactFlowId': contact_flow_id,
            'InstanceId': connect_instance_id,
            'Attributes': attributes
        }
        
        # 添加可选参数（如果提供）
        if source_phone_number:
            params['SourcePhoneNumber'] = source_phone_number
        
        # 发起外呼电话
        response = connect_client.start_outbound_voice_contact(**params)
        
        print(f"成功发起外呼电话到 {phone_number}，ContactId: {response['ContactId']}")
        return response
        
    except Exception as e:
        print(f"发生未预期的错误: {str(e)}")
        raise

# 创建表单
with st.form("otp_form"):
    # 手机号码输入
    phone_number = st.text_input("请输入手机号码", 
                                placeholder="+18007282584",
                                value="+18007282584",
                                max_chars=12)
    
    # 生成验证码按钮
    if st.form_submit_button("生成验证码"):
        if not phone_number or len(phone_number) != 12:
            st.error("请输入有效的11位手机号码")
        else:
            # 在会话状态中保存验证码
            st.session_state.otp = generate_otp()
            st.session_state.phone = phone_number
            st.session_state.show_otp = True

# 如果已生成验证码，显示验证码和发送选项
if 'show_otp' in st.session_state and st.session_state.show_otp:
    st.success(f"为手机号 {st.session_state.phone} 生成的验证码: {st.session_state.otp}")
    
    # 初始化计时器状态
    if 'countdown_active' not in st.session_state:
        st.session_state.countdown_active = False
        st.session_state.countdown_time = 60
    
    # 创建列来放置按钮和倒计时
    col1, col2 = st.columns([1, 2])
    
    # 语音发送按钮
    with col1:
        if st.button("语音发送验证码", disabled=st.session_state.countdown_active):
            st.session_state.countdown_active = True
            st.session_state.countdown_time = 60
            st.session_state.start_time = time.time()
            
            # 模拟发送验证码
            st.toast(f"正在通过语音将验证码 {st.session_state.otp} 发送至 {st.session_state.phone}")
            
            # 
            start_outbound_voice_call(st.session_state.phone, st.session_state.otp,'b7e4b4ed-1bdf-4b14-b624-d9328f08725a','f405040b-7b51-43c9-8d94-7c5743f136a3','+13072633584')
    
    # 显示倒计时
    with col2:
        if st.session_state.countdown_active:
            # 计算剩余时间
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.countdown_time - int(elapsed))
            
            if remaining > 0:
                st.write(f"请等待 {remaining} 秒后重新发送")
            else:
                st.session_state.countdown_active = False

# 添加重置功能
if 'show_otp' in st.session_state and st.session_state.show_otp:
    if st.button("重置"):
        for key in ['otp', 'phone', 'show_otp', 'countdown_active', 'countdown_time', 'start_time']:
            if key in st.session_state:
                del st.session_state[key]

# 自动刷新以更新倒计时
if 'countdown_active' in st.session_state and st.session_state.countdown_active:
    elapsed = time.time() - st.session_state.start_time
    if elapsed >= st.session_state.countdown_time:
        st.session_state.countdown_active = False
