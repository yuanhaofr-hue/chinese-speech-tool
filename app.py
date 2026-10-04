import streamlit as st
import edge_tts
import asyncio
import tempfile
import os

# 页面标题与配置
st.set_page_config(page_title="汉语语音检测小工具", page_icon="🎙️")
st.title("🎙️ 汉语语音检测与示范小工具")
st.write("输入文本生成标准范本，学生可录音并对比学习。")

# 1. 教师/示范区
st.header("1. 生成范本朗读")
text_input = st.text_area("请输入要练习的汉语文本：", "你好，欢迎来到汉语学习课堂。")
voice_option = st.selectbox("选择发音人：", ["zh-CN-XiaoxiaoNeural (女声)", "zh-CN-YunxiNeural (男声)"])

# 提取发音人 ID
voice_id = "zh-CN-XiaoxiaoNeural" if "Xiaoxiao" in voice_option else "zh-CN-YunxiNeural"

# 异步生成 TTS 函数
async def generate_audio(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name

if st.button("🔊 生成示范朗读"):
    if text_input.strip():
        with st.spinner("正在生成语音..."):
            audio_path = asyncio.run(generate_audio(text_input, voice_id))
            st.audio(audio_path, format="audio/mp3")
            st.success("示范语音生成成功！")
    else:
        st.warning("请输入有效的文本内容。")

st.divider()

# 2. 学生录音与评测区
st.header("2. 学生录音与评测")
st.write("请点击下方麦克风录制你的朗读：")

# 使用 Streamlit 官方录音组件
student_audio = st.audio_input("录制你的发音")

if student_audio:
    st.write("你的录音音频：")
    st.audio(student_audio)
    
    if st.button("📊 开始打分评估"):
        # 预留的评测逻辑接口
        # 实际生产中在此处调用科大讯飞/Azure等评测 API
        st.info("💡 评测功能演示：")
        st.metric(label="综合发音得分", value="88 分")
        
        st.subheader("详细指标：")
        col1, col2, col3 = st.columns(3)
        col1.metric("声调准确度", "85%")
        col2.metric("发音完整度", "92%")
        col3.metric("语速流畅度", "88%")
        
        st.success("提示：注意‘欢迎’的第二声调，发音可以更饱满一些！")